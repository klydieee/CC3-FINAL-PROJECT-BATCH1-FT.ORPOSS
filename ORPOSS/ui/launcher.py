"""
ui/launcher.py — Machine role selector & system dashboard.
Replaces the login screen as the first thing you see.
Saves the selected role to .role so the machine remembers next launch.
"""
import tkinter as tk
import customtkinter as ctk
import threading
import os
import sys

from utils.palette import palette

ROLE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".role")

ROLES = [
    {
        "key":     "pos",
        "label":   "POS TERMINAL",
        "icon":    "🖥",
        "desc":    "Customer ordering & payment",
        "color":   palette.primary,
        "pin":     None,   # no PIN — public-facing
    },
    {
        "key":     "kitchen",
        "label":   "KITCHEN PANEL",
        "icon":    "🍳",
        "desc":    "Order queue & status management",
        "color":   palette.secondary,
        "pin":     ["kitchen123", "k123", "123"],
    },
    {
        "key":     "orderstatus",
        "label":   "ORDER STATUS",
        "icon":    "📺",
        "desc":    "Customer-facing order display",
        "color":   "#9b59b6",
        "pin":     None,
    },
    {
        "key":     "admin",
        "label":   "ADMIN PANEL",
        "icon":    "⚙",
        "desc":    "Inventory, reports & analytics",
        "color":   palette.danger,
        "pin":     ["admin123", "a123", "123"],
    },
]


def _save_role(key):
    try:
        with open(ROLE_FILE, "w") as f:
            f.write(key)
    except:
        pass


def _load_role():
    try:
        if os.path.exists(ROLE_FILE):
            return open(ROLE_FILE).read().strip()
    except:
        pass
    return None


def _launch_role(window, key):
    from ui.login import start_login
    from ui.kitchen_panel import start_kitchen_panel
    from ui.order_status_window import open_order_status_window
    from ui.admin_panel import start_admin_panel

    _save_role(key)

    if key == "pos":
        start_login(window)
    elif key == "kitchen":
        start_kitchen_panel(window)
    elif key == "orderstatus":
        # Clear window, show fullscreen order status
        for w in window.winfo_children():
            w.destroy()
        open_order_status_window(window, allow_status_update=False)
        # Show a minimal host frame so the window isn't blank
        tk.Label(window, text="ORDER STATUS DISPLAY",
                 font=("Segoe UI", 14, "bold"),
                 bg=palette.bg, fg=palette.text).pack(expand=True)
    elif key == "admin":
        start_admin_panel(window, back_to_pos_callback=lambda: start_launcher(window))


def _ask_pin_then_launch(window, role):
    """Show PIN dialog for protected roles, then launch."""
    if not role["pin"]:
        _launch_role(window, role["key"])
        return

    popup = tk.Toplevel(window)
    popup.title(f"{role['label']} Access")
    popup.geometry("300x360")
    popup.configure(bg=palette.bg)
    popup.resizable(False, False)
    popup.transient(window)
    popup.grab_set()

    x = window.winfo_x() + window.winfo_width()  // 2 - 150
    y = window.winfo_y() + window.winfo_height() // 2 - 180
    popup.geometry(f"+{x}+{y}")

    tk.Label(popup, text=role["icon"], font=("Arial", 32),
             bg=palette.bg).pack(pady=(28, 4))
    tk.Label(popup, text=role["label"], font=("Helvetica", 13, "bold"),
             bg=palette.bg, fg=palette.text).pack()
    tk.Label(popup, text="Enter PIN to continue", font=("Helvetica", 9),
             bg=palette.bg, fg="#7f8c8d").pack(pady=(4, 16))

    pass_var = tk.StringVar()
    entry = tk.Entry(popup, textvariable=pass_var, font=("Helvetica", 18),
                     show="●", justify="center", bd=0, bg=palette.win95, width=14)
    entry.pack(ipady=10)
    entry.focus_set()
    tk.Frame(popup, height=2, width=180, bg=palette.text).pack(pady=(0, 8))

    err_lbl = tk.Label(popup, text="", font=("Helvetica", 8),
                       bg=palette.bg, fg=palette.danger)
    err_lbl.pack()

    def verify():
        if pass_var.get() in role["pin"]:
            popup.destroy()
            _launch_role(window, role["key"])
        else:
            pass_var.set("")
            err_lbl.config(text="Incorrect PIN. Try again.")

    btn_row = tk.Frame(popup, bg=palette.bg)
    btn_row.pack(side="bottom", fill="x", pady=16)
    tk.Button(btn_row, text="CANCEL", font=("Helvetica", 9, "bold"),
              bg=palette.bg, fg=palette.text, relief="flat",
              cursor="hand2", command=popup.destroy
              ).pack(side="left", padx=24)
    tk.Button(btn_row, text="ENTER", font=("Helvetica", 9, "bold"),
              bg=palette.text, fg="white", relief="flat",
              width=10, height=2, cursor="hand2", command=verify
              ).pack(side="right", padx=24)
    popup.bind("<Return>", lambda e: verify())


def start_launcher(window):
    for w in window.winfo_children():
        w.destroy()

    if isinstance(window, ctk.CTk):
        window.configure(fg_color=palette.bg)
    else:
        window.configure(bg=palette.bg)

    # ── Header ────────────────────────────────────────────────────────────────
    header = tk.Frame(window, bg=palette.text, height=70)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="ORPOSS",
             font=("Helvetica", 26, "bold"), fg=palette.bg, bg=palette.text
             ).pack(side="left", padx=28)
    tk.Label(header, text="Ordering & Point of Sales System",
             font=("Helvetica", 10), fg="#95a5a6", bg=palette.text
             ).pack(side="left", padx=(0, 28))

    # Connection status badge (top right)
    conn_lbl = tk.Label(header, text="⏳  Connecting…",
                        font=("Segoe UI", 9, "bold"),
                        fg="white", bg=palette.text, padx=14, pady=6)
    conn_lbl.pack(side="right", padx=20)

    def update_conn_status():
        from db.connection import active_mode, is_online
        if is_online():
            mode = active_mode() or "Online"
            conn_lbl.config(text=f"●  {mode}", fg=palette.secondary)
        else:
            conn_lbl.config(text="●  Offline", fg=palette.danger)

    threading.Thread(target=lambda: window.after(100, update_conn_status),
                     daemon=True).start()

    # ── Body ──────────────────────────────────────────────────────────────────
    body = tk.Frame(window, bg=palette.bg)
    body.pack(fill="both", expand=True)

    # Center container
    center = tk.Frame(body, bg=palette.bg)
    center.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(center, text="Select Terminal Mode",
             font=("Helvetica", 15), bg=palette.bg, fg="#7f8c8d"
             ).pack(pady=(0, 32))

    # Role buttons
    btn_grid = tk.Frame(center, bg=palette.bg)
    btn_grid.pack()

    last_role = _load_role()

    for i, role in enumerate(ROLES):
        col = i % 2
        row = i // 2

        card = tk.Frame(btn_grid, bg="white", width=260, height=130,
                        cursor="hand2")
        card.grid(row=row, column=col, padx=12, pady=12)
        card.pack_propagate(False)

        # Accent bar on left
        accent = tk.Frame(card, bg=role["color"], width=6)
        accent.pack(side="left", fill="y")

        inner = tk.Frame(card, bg="white")
        inner.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        top_row = tk.Frame(inner, bg="white")
        top_row.pack(fill="x")

        tk.Label(top_row, text=role["icon"], font=("Arial", 22),
                 bg="white").pack(side="left")

        # "Last used" badge
        if last_role == role["key"]:
            tk.Label(top_row, text="LAST USED", font=("Segoe UI", 7, "bold"),
                     bg=role["color"], fg="white", padx=6, pady=2
                     ).pack(side="right")

        tk.Label(inner, text=role["label"], font=("Segoe UI", 12, "bold"),
                 bg="white", fg=palette.text, anchor="w").pack(fill="x")
        tk.Label(inner, text=role["desc"], font=("Segoe UI", 9),
                 bg="white", fg="#7f8c8d", anchor="w", wraplength=190
                 ).pack(fill="x")

        if role["pin"]:
            tk.Label(inner, text="🔒 PIN required", font=("Segoe UI", 8),
                     bg="white", fg="#95a5a6").pack(anchor="w", pady=(4, 0))

        # Bind click on whole card
        def on_click(r=role):
            _ask_pin_then_launch(window, r)

        for widget in [card, inner, top_row] + list(inner.winfo_children()):
            try:
                widget.bind("<Button-1>", lambda e, r=role: on_click(r))
                widget.config(cursor="hand2")
            except:
                pass
        card.bind("<Button-1>", lambda e, r=role: on_click(r))

    # ── Footer ────────────────────────────────────────────────────────────────
    footer = tk.Frame(window, bg=palette.bg, pady=10)
    footer.pack(side="bottom", fill="x")
    tk.Label(footer, text="ORPOSS  •  CC3 Final Project  •  Batch 1",
             font=("Segoe UI", 8), bg=palette.bg, fg="#bdc3c7").pack()
