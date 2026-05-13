import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from ui.order_type import start_order_type

# ── colour palette (matches dashboard / admin panel) ──────────────────────────
BG        = "#ffffff"
TEXT      = "#2c3e50"
GREEN     = "#27ae60"
LIGHT_BG  = "#f5f6fa"
MUTED     = "#95a5a6"
MUTED_TXT = "#bdc3c7"

def start_login(window):
    """Render the ORPOSS landing / login screen inside *window*."""
    for w in window.winfo_children():
        w.destroy()

    window.configure(fg_color=BG)          # CTk root uses fg_color

    # ── centre container ──────────────────────────────────────────────────────
    container = tk.Frame(window, bg=BG)
    container.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(container, text="ORPOSS",
             font=("Helvetica", 52, "bold"), bg=BG, fg=TEXT).pack()

    tk.Label(container, text="Fresh Food. Fast Service.",
             font=("Helvetica", 14), bg=BG, fg=MUTED).pack(pady=(0, 50))

    tk.Button(
        container,
        text="START ORDER  ▶",
        font=("Helvetica", 18, "bold"),
        bg=GREEN, fg="white",
        activebackground="#2ecc71", activeforeground="white",
        relief="flat", padx=50, pady=20, cursor="hand2",
        command=lambda: start_order_type(window, user_role="Client")
    ).pack()

    # ── admin login (bottom-right corner) ─────────────────────────────────────
    def open_admin_login():
        win = tk.Toplevel(window)
        win.title("Admin Access")
        win.geometry("320x400")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(window)
        win.grab_set()

        x = window.winfo_x() + window.winfo_width()  // 2 - 160
        y = window.winfo_y() + window.winfo_height() // 2 - 200
        win.geometry(f"+{x}+{y}")

        tk.Label(win, text="🔒", font=("Arial", 30), bg=BG).pack(pady=(30, 10))
        tk.Label(win, text="ADMIN ACCESS",
                 font=("Helvetica", 12, "bold"), bg=BG, fg=TEXT).pack()
        tk.Label(win, text="Enter your secure PIN",
                 font=("Helvetica", 9), bg=BG, fg="#7f8c8d").pack(pady=(0, 20))

        pass_var = tk.StringVar()
        tk.Entry(win, textvariable=pass_var, font=("Helvetica", 18),
                 show="●", justify="center", bd=0, bg=LIGHT_BG, width=15
                 ).pack(ipady=10)
        tk.Frame(win, height=2, width=200, bg=TEXT).pack(pady=(0, 20))

        error_lbl = tk.Label(win, text="", font=("Helvetica", 8),
                              bg=BG, fg="#e74c3c")
        error_lbl.pack()

        def verify():
            if pass_var.get() == "admin123" or "123":
                win.destroy()
                start_order_type(window, user_role="Admin")
            else:
                pass_var.set("")
                error_lbl.config(text="Incorrect password. Try again.")

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(side="bottom", fill="x", pady=20)
        tk.Button(btn_row, text="CANCEL", font=("Helvetica", 9, "bold"),
                  bg=BG, fg=MUTED, relief="flat",
                  command=win.destroy, cursor="hand2").pack(side="left", padx=30)
        tk.Button(btn_row, text="LOGIN", font=("Helvetica", 9, "bold"),
                  bg=TEXT, fg="white", relief="flat", width=12, height=2,
                  command=verify, cursor="hand2").pack(side="right", padx=30)
        win.bind("<Return>", lambda e: verify())

    tk.Button(
        window,
        text="ADMIN SETTINGS",
        font=("Helvetica", 8, "bold"),
        bg=LIGHT_BG, fg=MUTED_TXT,
        activebackground=LIGHT_BG, activeforeground=TEXT,
        relief="flat", padx=10, pady=5, cursor="hand2",
        command=open_admin_login
    ).place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
