"""
db/connection.py — MySQL connection with Aiven SSL support.
Reads credentials from .env. Works with any cloud MySQL (Aiven, PlanetScale, etc.)
Falls back gracefully if DB is unreachable (offline mode).
"""
import os
import threading

_lock = threading.Lock()
_conn = None
_offline = False


def _load_env():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    key = k.strip()
                    value = v.strip().strip("'").strip('"')
                    os.environ[key] = value
                    env[key] = value
    return env


def get_connection():
    global _conn, _offline
    if _offline:
        return None
    with _lock:
        try:
            import mysql.connector
            if _conn is None or not _conn.is_connected():
                env = _load_env()

                config = dict(
                    host       = env.get("DB_HOST", "localhost"),
                    port       = int(env.get("DB_PORT", 3306)),
                    user       = env.get("DB_USER", "root"),
                    password   = env.get("DB_PASSWORD", ""),
                    database   = env.get("DB_NAME", "ORPOSS"),
                    autocommit = True,
                    connection_timeout = 8,
                )

                # Aiven requires SSL — enable it when a CA cert path is provided
                ssl_ca = env.get("DB_SSL_CA", "")
                if ssl_ca:
                    config["ssl_ca"]      = ssl_ca
                    config["ssl_verify_cert"] = True

                _conn = mysql.connector.connect(**config)
                print(f"[DB] Connected to {config['host']}:{config['port']}")
            return _conn
        except Exception as e:
            print(f"[DB] Connection failed — running offline: {e}")
            _offline = True
            return None


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
