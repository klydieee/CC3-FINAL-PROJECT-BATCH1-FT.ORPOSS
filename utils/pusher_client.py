"""
utils/pusher_client.py
Wraps Pusher server-side SDK. Silently no-ops if unavailable.
Also exposes subscribe() for the client-side (pusher-py).
"""
import os
import threading

_pusher = None
_pusher_client = None
_initialized = False

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
                    env[k.strip()] = v.strip()
    return env

def _init():
    global _pusher, _initialized
    if _initialized:
        return
    _initialized = True
    try:
        import pusher
        env = _load_env()
        _pusher = pusher.Pusher(
            app_id  = env.get("PUSHER_APP_ID", ""),
            key     = env.get("PUSHER_KEY", ""),
            secret  = env.get("PUSHER_SECRET", ""),
            cluster = env.get("PUSHER_CLUSTER", "ap1"),
            ssl     = True,
        )
        print("[Pusher] Server client ready.")
    except Exception as e:
        print(f"[Pusher] Server init failed (offline mode): {e}")
        _pusher = None

def push_event(channel, event, data):
    """Fire a Pusher event in a background thread (non-blocking)."""
    def _fire():
        _init()
        if _pusher:
            try:
                _pusher.trigger(channel, event, data)
            except Exception as e:
                print(f"[Pusher] trigger failed: {e}")
    threading.Thread(target=_fire, daemon=True).start()


# ── Client-side subscription ──────────────────────────────────────────────────
def subscribe(channel, event, callback):
    """
    Subscribe to a Pusher channel/event.
    callback(data) is called in a background thread whenever the event fires.
    Uses pysher (pip install pysher).
    """
    def _connect():
        try:
            import pysher
            env = _load_env()
            client = pysher.Pusher(
                key     = env.get("PUSHER_KEY", ""),
                cluster = env.get("PUSHER_CLUSTER", "ap1"),
                secure  = True,
            )
            def on_connect(data):
                ch = client.subscribe(channel)
                ch.bind(event, callback)

            client.connection.bind("pusher:connection_established", on_connect)
            client.connect()
        except Exception as e:
            print(f"[Pusher] Client subscribe failed: {e}")

    threading.Thread(target=_connect, daemon=True).start()
