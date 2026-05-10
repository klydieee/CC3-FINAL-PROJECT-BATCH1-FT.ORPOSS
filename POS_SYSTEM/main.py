import os
from ui.login import start_login

if __name__ == "__main__":
    # Create necessary directories at startup
    if not os.path.exists("receipts"):
        os.makedirs("receipts")

    start_login()