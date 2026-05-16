"""
db/connection.py — MySQL connection with fallback chain + Store & Forward.

Connection priority
-------------------
  1. LAN MySQL (XAMPP on server PC) — fastest, works without internet
  2. Aiven cloud MySQL              — works with internet, no LAN needed
  3. Offline → writes go to offline_queue.json (Store & Forward)

Set DB_MODE=lan, DB_MODE=cloud, or DB_MODE=auto (default) in .env.

Store & Forward
---------------
While offline every mutating call is queued to offline_queue.json.
A background thread polls every RECONNECT_INTERVAL seconds.
The moment a connection succeeds the queue is flushed automatically.
"""
import os
import threading
import time

_lock          = threading.Lock()
_conn          = None
_offline       = False
_active_mode   = None
_flush_done    = False   # guard so we only flush once per reconnect event


_stop_reconnect_event = threading.Event()
_is_connected = False
RECONNECT_INTERVAL = 120  # seconds between reconnection attempts while offline


# ── .env loader ───────────────────────────────────────────────────────────────

def _load_env():
    base     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    key   = k.strip()
                    value = v.strip().strip("'").strip('"')
                    os.environ[key] = value
                    env[key] = value
    return env


# ── schema migrations ─────────────────────────────────────────────────────────

def _run_migrations(conn):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS `order_items` (
          `id`        INT           NOT NULL AUTO_INCREMENT,
          `name`      VARCHAR(100)  NOT NULL,
          `price`     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
          `stock`     INT           NOT NULL DEFAULT 0,
          `image_url` VARCHAR(500)  DEFAULT NULL,
          `cost`      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
          `category`  VARCHAR(100)  DEFAULT 'All',
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    for col_sql in [
        "ALTER TABLE `order_items` ADD COLUMN IF NOT EXISTS `cost`     DECIMAL(10,2) NOT NULL DEFAULT 0.00",
        "ALTER TABLE `order_items` ADD COLUMN IF NOT EXISTS `category` VARCHAR(100)  DEFAULT 'All'",
    ]:
        try:
            cur.execute(col_sql)
        except Exception:
            pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS `orders` (
          `id`           INT          NOT NULL AUTO_INCREMENT,
          `invoice_no`   VARCHAR(20)  NOT NULL UNIQUE,
          `order_type`   ENUM('Dine-In','Take-Out') NOT NULL DEFAULT 'Dine-In',
          `payment_mode` ENUM('counter','kiosk')    NOT NULL DEFAULT 'counter',
          `total`        DECIMAL(10,2) NOT NULL,
          `cash`         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
          `change_amt`   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
          `status`       ENUM('preparing','serving','claimed','cancelled') NOT NULL DEFAULT 'preparing',
          `created_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `serving_at`   DATETIME DEFAULT NULL,
          `claimed_at`   DATETIME DEFAULT NULL,
          PRIMARY KEY (`id`),
          INDEX `idx_status`  (`status`),
          INDEX `idx_created` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    try:
        cur.execute("""
            ALTER TABLE `orders`
            MODIFY COLUMN `status`
            ENUM('preparing','serving','claimed','cancelled') NOT NULL DEFAULT 'preparing'
        """)
    except Exception:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS `order_lines` (
          `id`         INT           NOT NULL AUTO_INCREMENT,
          `invoice_no` VARCHAR(20)   NOT NULL,
          `name`       VARCHAR(100)  NOT NULL,
          `qty`        INT           NOT NULL,
          `price`      DECIMAL(10,2) NOT NULL,
          `product_id` INT           DEFAULT NULL,
          PRIMARY KEY (`id`),
          INDEX `idx_invoice` (`invoice_no`),
          FOREIGN KEY (`invoice_no`) REFERENCES `orders`(`invoice_no`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    try:
        cur.execute("ALTER TABLE `order_lines` ADD COLUMN IF NOT EXISTS `product_id` INT DEFAULT NULL")
    except Exception:
        pass

    cur.execute("SELECT COUNT(*) AS cnt FROM `order_items`")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO `order_items` (`name`, `price`, `stock`, `cost`, `category`) VALUES (%s,%s,%s,%s,%s)",
            [
                ('Burger',      55.00, 50, 30.00, 'Main'),
                ('Fries',       35.00, 50, 20.00, 'Sides'),
                ('Chicken',     99.00, 50, 60.00, 'Main'),
                ('Soda',        25.00, 50, 15.00, 'Drinks'),
                ('Hotdog',      40.00, 50, 25.00, 'Main'),
                ('Ice Cream',   35.00, 50, 20.00, 'Dessert'),
                ('Extra Gravy', 15.00, 50, 10.00, 'Sides'),
                ('Extra Rice',  20.00, 50, 12.00, 'Sides'),
            ]
        )
        conn.commit()
        print("[DB] Tables created and seeded with default menu items.")
    else:
        print("[DB] Schema OK.")
    cur.close()


# ── low-level connect ─────────────────────────────────────────────────────────

def _try_connect(config, label):
    import mysql.connector
    conn = mysql.connector.connect(**config)
    print(f"[DB] Connected via {label} → {config['host']}:{config['port']}")
    _run_migrations(conn)
    return conn


def _build_configs(env):
    db_name = env.get("DB_NAME", "ORPOSS")
    timeout = 5

    lan_config = dict(
        host               = env.get("DB_HOST_LAN", "localhost"),
        port               = int(env.get("DB_PORT_LAN", 3306)),
        user               = env.get("DB_USER_LAN", "root"),
        password           = env.get("DB_PASSWORD_LAN", ""),
        database           = db_name,
        autocommit         = True,
        connection_timeout = timeout,
    )

    cloud_config = dict(
        host               = env.get("DB_HOST", ""),
        port               = int(env.get("DB_PORT", 3306)),
        user               = env.get("DB_USER", "root"),
        password           = env.get("DB_PASSWORD", ""),
        database           = db_name,
        autocommit         = True,
        connection_timeout = timeout,
    )
    ssl_ca = env.get("DB_SSL_CA", "")
    if ssl_ca and not os.path.isabs(ssl_ca):
        ssl_ca = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ssl_ca)
    if ssl_ca:
        cloud_config["ssl_ca"]          = ssl_ca
        cloud_config["ssl_verify_cert"] = True

    mode = env.get("DB_MODE", "auto").lower()
    if mode == "lan":
        return [("LAN", lan_config)]
    elif mode == "cloud":
        return [("Cloud/Aiven", cloud_config)]
    else:
        return [("LAN", lan_config), ("Cloud/Aiven", cloud_config)]


# ── public connection API ─────────────────────────────────────────────────────

def get_connection():
    global _conn, _offline, _active_mode
    with _lock:
        try:
            import mysql.connector
            if _conn is not None and _conn.is_connected():
                return _conn

            env      = _load_env()
            attempts = _build_configs(env)
            last_err = None

            for label, cfg in attempts:
                try:
                    _conn        = _try_connect(cfg, label)
                    _active_mode = label
                    _offline     = False
                    return _conn
                except Exception as e:
                    print(f"[DB] {label} failed: {e}")
                    last_err = e

            raise last_err

        except Exception as e:
            print(f"[DB] All connections failed — running offline: {e}")
            _offline = True
            return None


def active_mode():
    return _active_mode


def is_online():
    """Returns True if a live DB connection currently exists."""
    if _offline:
        return False
    return _conn is not None and _conn.is_connected()


def execute(query, params=None, fetch=None):
    conn = get_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        if fetch == "one":
            return cur.fetchone()
        if fetch == "all":
            return cur.fetchall()
        return cur.lastrowid
    except Exception as e:
        print(f"[DB] Query error: {e}")
        return None


# ── background reconnect + auto-flush ────────────────────────────────────────

def _reconnect_worker():
    """
    Polls for a DB connection while the app is offline.
    The moment one succeeds the offline queue is flushed.
    Runs as a daemon thread so it dies with the main process.
    """

    global _conn, _offline, _flush_done
    
    # 1. Clear the event flag so the loop is active
    _stop_reconnect_event.clear()

    # Loop runs ONLY while we want it to watch for a reconnect
    while not _stop_reconnect_event.is_set():
        
        # Instead of time.sleep(), this waits but can be interrupted instantly
        _stop_reconnect_event.wait(timeout=RECONNECT_INTERVAL)
        if _stop_reconnect_event.is_set():
            break

        # If we are already online, this thread shouldn't even be running.
        # But if we check and it's suddenly online, we handle the flush and kill the thread.
        if is_online():
            print("[DB] System is online. Thread closing down.")
            _stop_reconnect_event.set()
            break

        print("[DB] Attempting reconnect …")
        conn = get_connection()

        # If connection succeeds, lock it down, flush, and kill the thread
        if conn is not None:
            print("[DB] Reconnected! Flushing offline queue …")
            
            _conn = conn      # Update your global connection reference
            _offline = False  # Mark system as no longer offline
            
            # Run your flush function safely
            _do_flush()
            
            # CRUCIAL: Stop the thread now that we are online and flushed!
            print("[DB] Queue flushed successfully. Disabling reconnect watcher.")
            _stop_reconnect_event.set()
            break

    print("[DB] Reconnect watcher thread has safely exited.")


def _do_flush():
    """Import lazily to avoid circular imports at module load time."""
    try:
        from db.offline_queue import flush_queue, pending_count
        from db.products_db   import inventory
        n = pending_count()
        if n == 0:
            print("[DB] Queue is empty — nothing to flush.")
            return
        print(f"[DB] Flushing {n} queued operation(s) …")
        flushed = flush_queue(execute, inventory)
        if flushed:
            from db.products_db import load_inventory
            load_inventory()
    except Exception as e:
        print(f"[DB] Queue flush error: {e}")


def start_reconnect_watcher():
    """Call once from main.py after the initial connection attempt."""
    _stop_reconnect_event.clear()  # Ensure the flag is reset to "Go"
    
    t = threading.Thread(target=_reconnect_worker, daemon=True, name="db-reconnect-watcher")
    t.start()
    print(f"[DB] Reconnect watcher started (interval={RECONNECT_INTERVAL}s).")