import os
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import customtkinter as ctk
from ui.launcher import start_launcher
from db.connection import get_connection
from db.products_db import load_inventory
from db.orders_db import get_orders


def main():
    get_connection()
    load_inventory()
    get_orders()

    root = ctk.CTk()
    root.title("ORPOSS — Ordering & Point of Sales System")
    width, height = 1200, 700
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")

    try:
        root.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico"))
    except:
        pass

    start_launcher(root)
    root.mainloop()


if __name__ == "__main__":
    main()