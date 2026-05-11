import tkinter as tk
import customtkinter as ctk

BG    = "#ffffff"
TEXT  = "#2c3e50"
MUTED = "#95a5a6"

def start_order_type(window, user_role="Client"):
    """Screen 2 — choose Dine-In or Take-Out, then proceed to dashboard."""
    from ui.dashboard import start_dashboard
    from ui.login import start_login

    for w in window.winfo_children():
        w.destroy()

    window.configure(fg_color=BG)

    # ── back button (top-left) ────────────────────────────────────────────────
    tk.Button(
        window, text="← BACK",
        font=("Helvetica", 9, "bold"),
        bg=BG, fg=MUTED, activeforeground=TEXT,
        relief="flat", cursor="hand2",
        command=lambda: start_login(window)
    ).place(x=20, y=20)

    # ── centre content ────────────────────────────────────────────────────────
    container = tk.Frame(window, bg=BG)
    container.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(container, text="How will you be dining?",
             font=("Helvetica", 28, "bold"), bg=BG, fg=TEXT).pack(pady=(0, 8))
    tk.Label(container, text="Choose an option to continue.",
             font=("Helvetica", 13), bg=BG, fg=MUTED).pack(pady=(0, 50))

    cards_row = tk.Frame(container, bg=BG)
    cards_row.pack()

    def make_card(parent, emoji, label, color, hover, order_type):
        f = tk.Frame(parent, bg=color, width=220, height=220,
                     cursor="hand2", bd=0, relief="flat")
        f.pack_propagate(False)
        f.pack(side="left", padx=24)

        inner = tk.Frame(f, bg=color)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(inner, text=emoji, font=("Arial", 48), bg=color).pack()
        tk.Label(inner, text=label, font=("Helvetica", 16, "bold"),
                 bg=color, fg="white").pack(pady=(8, 0))

        def on_enter(e): f.config(bg=hover); inner.config(bg=hover)
        def on_leave(e): f.config(bg=color); inner.config(bg=hover if False else color)
        def on_click(e): start_dashboard(window, user_role=user_role, order_type=order_type)

        for w in [f, inner] + inner.winfo_children():
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    make_card(cards_row, "🍽️", "DINE IN",  "#2c3e50", "#34495e", "Dine-In")
    make_card(cards_row, "🥡", "TAKE OUT", "#e67e22", "#d35400", "Take-Out")
