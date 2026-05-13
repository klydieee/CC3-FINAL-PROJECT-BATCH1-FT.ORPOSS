import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

# ── IMPORTS ──────────────────────────────────────────────────────────────────
from ui.order_type import start_order_type
from ui.kitchen_panel import start_kitchen_panel
from utils.palette import palette


def start_login(window):
    """Render the ORPOSS landing / login screen inside *window*."""
    for w in window.winfo_children():
        w.destroy()

    # Using lowercase palette.bg
    window.configure(fg_color=palette.bg)

    # ── CENTRE CONTAINER ──────────────────────────────────────────────────────
    container = tk.Frame(window, bg=palette.bg)
    container.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(container, text="ORPOSS",
             font=("Helvetica", 52, "bold"), bg=palette.bg, fg=palette.text).pack()

    tk.Label(container, text="Fresh Food. Fast Service.",
             font=("Helvetica", 14), bg=palette.bg, fg=palette.text).pack(pady=(0, 50))

    tk.Button(
        container,
        text="START ORDER  ▶",
        font=("Helvetica", 18, "bold"),
        bg=palette.secondary, fg="white",
        activebackground="#2ecc71", activeforeground="white",
        relief="flat", padx=50, pady=20, cursor="hand2",
        command=lambda: start_order_type(window, user_role="Client")
    ).pack()

    # ── REUSABLE LOGIN POPUP ──────────────────────────────────────────────────
    def open_access_popup(title, icon, role):
        """Creates a secure PIN entry window for Admin or Kitchen."""
        win = tk.Toplevel(window)
        win.title(title)
        win.geometry("320x400")
        win.configure(bg=palette.bg)
        win.resizable(False, False)
        win.transient(window)
        win.grab_set()

        # Center on parent
        x = window.winfo_x() + window.winfo_width() // 2 - 160
        y = window.winfo_y() + window.winfo_height() // 2 - 200
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text=icon, font=("Arial", 30), bg=palette.bg).pack(pady=(30, 10))
        tk.Label(win, text=title.upper(), font=("Helvetica", 12, "bold"),
                 bg=palette.bg, fg=palette.text).pack()
        tk.Label(win, text="Enter your secure PIN", font=("Helvetica", 9),
                 bg=palette.bg, fg="#7f8c8d").pack(pady=(0, 20))

        pass_var = tk.StringVar()
        entry = tk.Entry(win, textvariable=pass_var, font=("Helvetica", 18),
                         show="●", justify="center", bd=0, bg=palette.win95, width=15)
        entry.pack(ipady=10)
        entry.focus_set()

        tk.Frame(win, height=2, width=200, bg=palette.text).pack(pady=(0, 20))

        error_lbl = tk.Label(win, text="", font=("Helvetica", 8), bg=palette.bg, fg=palette.danger)
        error_lbl.pack()

        def verify():
            pin = pass_var.get()
            if role == "Admin" and pin in ["admin123", "a123"]:
                win.destroy()
                start_order_type(window, user_role="Admin")
            elif role == "Kitchen" and pin in ["kitchen123", "k123"]:
                win.destroy()
                start_kitchen_panel(window)
            else:
                pass_var.set("")
                error_lbl.config(text="Incorrect PIN. Please try again.")

        btn_row = tk.Frame(win, bg=palette.bg)
        btn_row.pack(side="bottom", fill="x", pady=20)

        tk.Button(btn_row, text="CANCEL", font=("Helvetica", 9, "bold"),
                  bg=palette.bg, fg=palette.text, relief="flat",
                  command=win.destroy, cursor="hand2").pack(side="left", padx=30)

        tk.Button(btn_row, text="LOGIN", font=("Helvetica", 9, "bold"),
                  bg=palette.text, fg="white", relief="flat", width=12, height=2,
                  command=verify, cursor="hand2").pack(side="right", padx=30)

        win.bind("<Return>", lambda e: verify())

    # ── ACCESS BUTTONS (BOTTOM RIGHT) ──────────────────────────────────────────
    def open_admin_panel_direct():
        """Verify PIN then go straight to admin panel, skipping POS."""
        win = tk.Toplevel(window)
        win.title("Admin Panel Access")
        win.geometry("320x400")
        win.configure(bg=palette.bg)
        win.resizable(False, False)
        win.transient(window)
        win.grab_set()
        x = window.winfo_x() + window.winfo_width()  // 2 - 160
        y = window.winfo_y() + window.winfo_height() // 2 - 200
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="🖥️", font=("Arial", 30), bg=palette.bg).pack(pady=(30, 10))
        tk.Label(win, text="ADMIN PANEL", font=("Helvetica", 12, "bold"),
                 bg=palette.bg, fg=palette.text).pack()
        tk.Label(win, text="Enter your secure PIN", font=("Helvetica", 9),
                 bg=palette.bg, fg="#7f8c8d").pack(pady=(0, 20))

        pass_var = tk.StringVar()
        entry = tk.Entry(win, textvariable=pass_var, font=("Helvetica", 18),
                         show="●", justify="center", bd=0, bg=palette.win95, width=15)
        entry.pack(ipady=10)
        entry.focus_set()
        tk.Frame(win, height=2, width=200, bg=palette.text).pack(pady=(0, 20))
        err = tk.Label(win, text="", font=("Helvetica", 8), bg=palette.bg, fg=palette.danger)
        err.pack()

        def verify():
            if pass_var.get() in ["admin123", "a123"]:
                win.destroy()
                from ui.admin_panel import start_admin_panel
                start_admin_panel(window, back_to_pos_callback=lambda: start_login(window))
            else:
                pass_var.set("")
                err.config(text="Incorrect PIN.")

        btn_row = tk.Frame(win, bg=palette.bg)
        btn_row.pack(side="bottom", fill="x", pady=20)
        tk.Button(btn_row, text="CANCEL", font=("Helvetica", 9, "bold"),
                  bg=palette.bg, fg=palette.text, relief="flat",
                  command=win.destroy, cursor="hand2").pack(side="left", padx=30)
        tk.Button(btn_row, text="LOGIN", font=("Helvetica", 9, "bold"),
                  bg=palette.text, fg="white", relief="flat", width=12, height=2,
                  command=verify, cursor="hand2").pack(side="right", padx=30)
        win.bind("<Return>", lambda e: verify())

    # Kitchen Panel Button
    tk.Button(
        window,
        text="KITCHEN PANEL",
        font=("Helvetica", 8, "bold"),
        bg=palette.win95, fg=palette.text,
        activebackground=palette.win95, activeforeground=palette.text,
        relief="flat", padx=10, pady=5, cursor="hand2",
        command=lambda: open_access_popup("Kitchen Access", "👨‍🍳", "Kitchen")
    ).place(relx=1.0, rely=1.0, anchor="se", x=-150, y=-20)

    # Direct Admin Panel (skips POS)
    tk.Button(
        window,
        text="ADMIN PANEL",
        font=("Helvetica", 8, "bold"),
        bg=palette.win95, fg=palette.text,
        activebackground=palette.win95, activeforeground=palette.text,
        relief="flat", padx=10, pady=5, cursor="hand2",
        command=open_admin_panel_direct
    ).place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)