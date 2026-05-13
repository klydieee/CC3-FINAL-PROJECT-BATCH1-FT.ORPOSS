import tkinter as tk
from utils.palette import palette


def start_order_type(window, user_role="Client"):
    from ui.dashboard import start_dashboard
    from ui.login import start_login

    # Clear previous screen
    for widget in window.winfo_children():
        widget.destroy()

    window.configure(bg=palette.bg)

    tk.Button(
        window,
        text="← BACK",
        font=("Helvetica", 9, "bold"),
        bg=palette.bg,
        fg=palette.win95,
        activeforeground=palette.text,
        activebackground=palette.bg,
        relief="flat",
        cursor="hand2",
        command=lambda: start_login(window)
    ).place(x=20, y=20)

    container = tk.Frame(window, bg=palette.bg)
    container.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        container,
        text="How will you be dining?",
        font=("Helvetica", 28, "bold"),
        bg=palette.bg,
        fg=palette.text
    ).pack(pady=(0, 8))

    tk.Label(
        container,
        text="Choose an option to continue.",
        font=("Helvetica", 13),
        bg=palette.bg,
        fg=palette.win95
    ).pack(pady=(0, 50))

    cards_row = tk.Frame(container, bg=palette.bg)
    cards_row.pack()

    def make_card(parent, emoji, label, color, hover_color, order_type_val):
        # Outer card frame
        card_frame = tk.Frame(
            parent,
            bg=color,
            width=320,
            height=320,
            cursor="hand2",
            bd=0,
            relief="flat"
        )
        card_frame.pack_propagate(False)
        card_frame.pack(side="left", padx=24)

        # Inner container
        inner_content = tk.Frame(card_frame, bg=color)
        inner_content.place(relx=0.5, rely=0.5, anchor="center")

        # Emoji Label
        emoji_lbl = tk.Label(
            inner_content,
            text=emoji,
            font=("Segoe UI Emoji", 48),
            bg=color,
            fg="white",
            anchor="center"
        )
        emoji_lbl.pack(fill="x")

        # Text Label
        text_lbl = tk.Label(
            inner_content,
            text=label,
            font=("Helvetica", 16, "bold"),
            bg=color,
            fg="white",
            anchor="center"
        )
        text_lbl.pack(pady=(8, 0), fill="x")

        # Widget list
        widgets = [card_frame, inner_content, emoji_lbl, text_lbl]

        def on_enter(_event):
            for w in widgets:
                w.config(bg=hover_color)

        def on_leave(_event):
            for w in widgets:
                w.config(bg=color)

        def on_click(_event):
            start_dashboard(window, user_role=user_role, order_type=order_type_val)

        # Bind events
        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    # DINE IN
    make_card(cards_row, "🍽️", "DINE IN", palette.teal, palette.text, "Dine-In")
    # TAKE OUT
    make_card(cards_row, "🥡", "TAKE OUT", palette.primary, palette.danger, "Take-Out")