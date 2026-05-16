"""
utils/pusher_client.py
Wraps Pusher server-side SDK (push) and client-side (subscribe).
Uses a SINGLE persistent pysher client shared across all subscribers.
"""
import os
import threading

_pusher      = None
_initialized = False

# Single shared pysher client
_pysher_client    = None
_pysher_lock      = threading.Lock()
_pysher_connected = False
_pending_subs     = []   # (channel, event, callback) queued before connect


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
                    env[k.strip()] = v.strip()
    return env


def _init_server():
    global _pusher, _initialized
    if _initialized:
        return
    _initialized = True
    try:
        import pusher
        env     = _load_env()
        _pusher = pusher.Pusher(
            app_id  = env.get("PUSHER_APP_ID", ""),
            key     = env.get("PUSHER_KEY", ""),
            secret  = env.get("PUSHER_SECRET", ""),
            cluster = env.get("PUSHER_CLUSTER", "ap1"),
            ssl     = True,
        )
        print("[Pusher] Server client ready.")
    except Exception as e:
        print(f"[Pusher] Server init failed: {e}")
        _pusher = None


def push_event(channel, event, data):
    """Fire a Pusher event in a background thread (non-blocking)."""
    def _fire():
        _init_server()
        if _pusher:
            try:
                _pusher.trigger(channel, event, data)
            except Exception as e:
                print(f"[Pusher] trigger failed: {e}")
    threading.Thread(target=_fire, daemon=True).start()


# ── Single shared pysher client ───────────────────────────────────────────────

def _get_pysher():
    """Return the shared pysher client, creating it if needed."""
    global _pysher_client, _pysher_connected

    with _pysher_lock:
        if _pysher_client is not None:
            return _pysher_client
        try:
            import pysher
            env    = _load_env()
            client = pysher.Pusher(
                key     = env.get("PUSHER_KEY", ""),
                cluster = env.get("PUSHER_CLUSTER", "ap1"),
                secure  = True,
            )

            def on_connect(data):
                global _pysher_connected
                _pysher_connected = True
                print("[Pusher] Client connected.")
                # Flush pending subscriptions
                for ch_name, ev, cb in _pending_subs:
                    try:
                        ch = client.subscribe(ch_name)
                        ch.bind(ev, cb)
                    except Exception as e:
                        print(f"[Pusher] Late bind failed: {e}")
                _pending_subs.clear()

            client.connection.bind("pusher:connection_established", on_connect)
            client.connect()
            _pysher_client = client
            return client
        except Exception as e:
            print(f"[Pusher] Client init failed: {e}")
            return None


def subscribe(channel, event, callback):
    """
    Subscribe to a Pusher channel/event using the shared client.
    Safe to call multiple times — won't create duplicate connections.
    """
    def _do():
        client = _get_pysher()
        if client is None:
            return
        if _pysher_connected:
            try:
                ch = client.subscribe(channel)
                ch.bind(event, callback)
            except Exception as e:
                print(f"[Pusher] subscribe failed: {e}")
        else:
            # Queue it — will be bound once connected
            _pending_subs.append((channel, event, callback))

    threading.Thread(target=_do, daemon=True).start()
