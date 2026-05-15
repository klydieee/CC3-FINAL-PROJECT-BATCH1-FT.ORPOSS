"""
utils/image_storage.py
──────────────────────
Dual-mode image storage: Cloudinary (cloud) OR Local (disk).

Usage:
    from utils.image_storage import ImageStorage
    store = ImageStorage()           # reads .env on init
    url   = store.upload("path/to/file.jpg", public_id="product_name")
    store.delete("product_name")     # remove from active backend
    store.set_mode("local")          # switch at runtime
    store.set_mode("cloudinary")
"""

import os
import shutil
import threading

# ── Singleton lock ────────────────────────────────────────────────────────────
_lock = threading.Lock()


def _load_env() -> dict:
    """
    Search for .env in several candidate locations so we find it
    regardless of the working directory or how the app is launched.
    """
    candidates = [
        # 1. Two levels up from this file  (utils/ -> FINAL_POS/)
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        # 2. One level up from this file   (in case utils/ is at root)
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        # 3. Current working directory
        os.path.join(os.getcwd(), ".env"),
        # 4. Directory of the entry-point script (sys.argv[0])
        os.path.join(os.path.dirname(os.path.abspath(__import__("sys").argv[0])), ".env"),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            env = {}
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip()
            print(f"[ImageStorage] Loaded .env from: {env_path}", flush=True)
            return env
    print("[ImageStorage] WARNING: .env not found in any candidate path.")
    print("[ImageStorage] Searched:", candidates)
    return {}


def _save_env_key(key: str, value: str):
    """Persist a single key back to .env. Uses same search order as _load_env."""
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__import__("sys").argv[0])), ".env"),
    ]
    env_path = next((p for p in candidates if os.path.exists(p)), candidates[0])
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)


# ── Local images directory ────────────────────────────────────────────────────
def _local_images_dir() -> str:
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__import__("sys").argv[0])), ".env"),
    ]
    env_path = next((p for p in candidates if os.path.exists(p)), candidates[0])
    base = os.path.dirname(env_path)
    path = os.path.join(base, "data", "product_images")
    os.makedirs(path, exist_ok=True)
    return path


class ImageStorage:
    """
    Manages product image upload/delete with a hot-swappable backend.

    Modes
    -----
    "cloudinary"  – uploads via Cloudinary SDK; returns an HTTPS URL.
    "local"       – copies the file to data/product_images/; returns a
                    relative file:// path that the UI resolves at runtime.
    """

    _instance = None  # module-level singleton so all panels share state

    def __new__(cls):
        with _lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        env = _load_env()
        # Default to "cloudinary" if creds are present, else "local"
        default_mode = "cloudinary" if env.get("CLOUDINARY_CLOUD_NAME") else "local"
        self._mode = env.get("IMAGE_STORAGE_MODE", default_mode)
        self._cloudinary_configured = False
        self._try_configure_cloudinary(env)

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def cloudinary_ready(self) -> bool:
        return self._cloudinary_configured

    def set_mode(self, mode: str):
        """Switch between 'cloudinary' and 'local' at runtime."""
        if mode not in ("cloudinary", "local"):
            raise ValueError("mode must be 'cloudinary' or 'local'")
        if mode == "cloudinary" and not self._cloudinary_configured:
            # Try to configure with fresh env read
            self._try_configure_cloudinary(_load_env())
            if not self._cloudinary_configured:
                raise RuntimeError(
                    "Cloudinary credentials missing or invalid.\n"
                    "Fill CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, "
                    "CLOUDINARY_API_SECRET in your .env file."
                )
        self._mode = mode
        _save_env_key("IMAGE_STORAGE_MODE", mode)
        print(f"[ImageStorage] Mode: {mode}")

    def upload(self, file_path: str, public_id: str) -> str:
        """
        Upload an image and return its URL/path.

        Parameters
        ----------
        file_path : str  – absolute path to the source image file
        public_id : str  – logical name (e.g. product name, slugified)

        Returns
        -------
        str – URL (Cloudinary) or absolute file path (local)
        """
        if self._mode == "cloudinary":
            return self._upload_cloudinary(file_path, public_id)
        return self._upload_local(file_path, public_id)

    def delete(self, public_id: str):
        """Remove image from the active backend."""
        if self._mode == "cloudinary":
            self._delete_cloudinary(public_id)
        else:
            self._delete_local(public_id)

    def refresh_credentials(self):
        """Re-read .env and attempt to (re-)configure Cloudinary."""
        env = _load_env()
        self._try_configure_cloudinary(env)

    # ── Cloudinary backend ────────────────────────────────────────────────────

    def _try_configure_cloudinary(self, env: dict):
        cloud_name = env.get("CLOUDINARY_CLOUD_NAME", "")
        api_key    = env.get("CLOUDINARY_API_KEY", "")
        api_secret = env.get("CLOUDINARY_API_SECRET", "")
        if not (cloud_name and api_key and api_secret):
            self._cloudinary_configured = False
            return
        try:
            import cloudinary
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True,
            )
            self._cloudinary_configured = True
            print("[ImageStorage] Cloudinary configured ✓")
        except ImportError:
            print("[ImageStorage] cloudinary package not installed.")
            self._cloudinary_configured = False
        except Exception as e:
            print(f"[ImageStorage] Cloudinary config error: {e}")
            self._cloudinary_configured = False

    def _upload_cloudinary(self, file_path: str, public_id: str) -> str:
        import cloudinary.uploader
        slug = _slugify(public_id)
        result = cloudinary.uploader.upload(
            file_path,
            public_id=f"orposs/products/{slug}",
            overwrite=True,
            resource_type="image",
        )
        url = result.get("secure_url", "")
        print(f"[ImageStorage] Cloudinary upload -> {url}")
        return url

    def _delete_cloudinary(self, public_id: str):
        try:
            import cloudinary.uploader
            slug = _slugify(public_id)
            cloudinary.uploader.destroy(f"orposs/products/{slug}")
            print(f"[ImageStorage] Cloudinary deleted: {slug}")
        except Exception as e:
            print(f"[ImageStorage] Cloudinary delete error: {e}")

    # ── Local backend ─────────────────────────────────────────────────────────

    def _upload_local(self, file_path: str, public_id: str) -> str:
        slug = _slugify(public_id)
        ext  = os.path.splitext(file_path)[1].lower() or ".jpg"
        dest = os.path.join(_local_images_dir(), f"{slug}{ext}")
        shutil.copy2(file_path, dest)
        print(f"[ImageStorage] Local copy -> {dest}")
        return dest  # absolute path; UI opens via PIL

    def _delete_local(self, public_id: str):
        slug = _slugify(public_id)
        img_dir = _local_images_dir()
        for fname in os.listdir(img_dir):
            name, _ = os.path.splitext(fname)
            if name == slug:
                os.remove(os.path.join(img_dir, fname))
                print(f"[ImageStorage] Local deleted: {fname}")
                return


# ── helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """'Yum Burger' → 'yum_burger'"""
    return text.strip().lower().replace(" ", "_").replace("/", "_")
