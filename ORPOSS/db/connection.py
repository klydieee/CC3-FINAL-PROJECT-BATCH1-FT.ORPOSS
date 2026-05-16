"""
db/connection.py — MySQL connection with fallback chain:
  1. LAN MySQL (XAMPP on server PC) — fastest, works without internet
  2. Aiven cloud MySQL              — works with internet, no LAN needed
  3. Offline (inventory.py)         — read-only fallback

Set DB_MODE=lan, DB_MODE=cloud, or DB_MODE=auto (default) in .env.
"""
import os
import threading

_lock        = threading.Lock()
_conn        = None
_offline     = False
_active_mode = None


def _load_env():
    base     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v   = line.split("=", 1)
                    key    = k.strip()
                    value  = v.strip().strip("'").strip('"')
                    os.environ[key] = value
                    env[key] = value
    return env


def _run_migrations(conn):
    cur = conn.cursor()

    # ── order_items ───────────────────────────────────────────────────────────
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
    # Safe column additions for databases that existed before these columns
    for col_sql in [
        "ALTER TABLE `order_items` ADD COLUMN IF NOT EXISTS `cost`     DECIMAL(10,2) NOT NULL DEFAULT 0.00",
        "ALTER TABLE `order_items` ADD COLUMN IF NOT EXISTS `category` VARCHAR(100)  DEFAULT 'All'",
    ]:
        try:
            cur.execute(col_sql)
        except Exception:
            pass

    # ── orders ────────────────────────────────────────────────────────────────
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
    # Add 'cancelled' to status ENUM if this is an older DB
    try:
        cur.execute("""
            ALTER TABLE `orders`
            MODIFY COLUMN `status`
            ENUM('preparing','serving','claimed','cancelled') NOT NULL DEFAULT 'preparing'
        """)
    except Exception:
        pass

    # ── order_lines ───────────────────────────────────────────────────────────
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

    # ── Seed default menu if empty ────────────────────────────────────────────
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


def _try_connect(config, label):
    import mysql.connector
    conn = mysql.connector.connect(**config)
    print(f"[DB] Connected via {label} → {config['host']}:{config['port']}")
    _run_migrations(conn)
    return conn


def get_connection():
    global _conn, _offline, _active_mode
    if _offline:
        return None
    with _lock:
        try:
            import mysql.connector
            if _conn is not None and _conn.is_connected():
                return _conn

            env     = _load_env()
            mode    = env.get("DB_MODE", "auto").lower()
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

            if mode == "lan":
                attempts = [("LAN", lan_config)]
            elif mode == "cloud":
                attempts = [("Cloud/Aiven", cloud_config)]
            else:
                attempts = [("LAN", lan_config), ("Cloud/Aiven", cloud_config)]

            last_err = None
            for label, cfg in attempts:
                try:
                    _conn = _try_connect(cfg, label)
                    _active_mode = label
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
    return get_connection() is not None


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
