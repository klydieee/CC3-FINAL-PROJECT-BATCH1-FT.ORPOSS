"""
utils/sound.py — Simple sound player for ORPOSS.
Uses winsound (built-in Windows) — no pip install needed.
Drop your .wav files in assets/sounds/ and call play("filename.wav").
Note: winsound only supports .wav, not .mp3.
"""
import os
import threading

SOUNDS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "sounds"
)


def play(filename):
    """Play a .wav file non-blocking."""
    def _play():
        try:
            import winsound
            path = os.path.join(SOUNDS_DIR, filename)
            if not os.path.exists(path):
                print(f"[Sound] File not found: {path}")
                return
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print(f"[Sound] Failed to play {filename}: {e}")
    threading.Thread(target=_play, daemon=True).start()
