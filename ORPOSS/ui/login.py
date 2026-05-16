import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk

from ui.kitchen_panel import start_kitchen_panel
from ui.order_type import start_order_type
from utils.sound import play
from ui.launcher import start_launcher
from utils.palette import palette


def start_login(window):
    for w in window.winfo_children():
        w.destroy()

    window.configure(fg_color=palette.bg)

    container = tk.Frame(window, bg=palette.bg)
    container.place(relx=0.5, rely=0.5, anchor="center")

    logo_img = Image.open("assets/Logo.png")
    logo_img = logo_img.resize((70, 70), Image.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_img)

    title_row = tk.Frame(container, bg=palette.bg)
    title_row.pack()

    logo_label = tk.Label(title_row, image=logo_photo, bg=palette.bg)
    logo_label.image = logo_photo
    logo_label.pack(side="left", padx=(0, 10))

    tk.Label(
        title_row,
        text="ORPOSS",
        font=("Verdana", 52, "bold"),
        bg=palette.bg,
        fg=palette.text
    ).pack(side="left")

    tk.Label(
        container,
        text="Fresh Food. Fast Service.",
        font=("Helvetica", 14),
        bg=palette.bg,
        fg=palette.text
    ).pack(pady=(0, 50))

    tk.Button(
        container,
        text="START ORDER  ▶",
        font=("Helvetica", 18, "bold"),
        bg=palette.secondary,
        fg="white",
        activebackground="#2ecc71",
        activeforeground="white",
        relief="flat",
        padx=50,
        pady=20,
        cursor="hand2",
        command=lambda: [play("PopOpen.wav"), start_order_type(window, user_role="Client")]
    ).pack()

    def open_access_popup(title, icon, role):
        win = tk.Toplevel(window)
        win.title(title)
        win.geometry("320x400")
        win.configure(bg=palette.bg)
        win.resizable(False, False)
        win.transient(window)
        win.grab_set()

        x = window.winfo_x() + window.winfo_width() // 2 - 160
        y = window.winfo_y() + window.winfo_height() // 2 - 200
        win.geometry(f"+{x}+{y}")

        icon_frame = tk.Frame(win, bg=palette.bg)
        icon_frame.pack(fill="x", pady=(30, 10))

        tk.Label(
            icon_frame,
            text=icon,
            font=("Arial", 30),
            bg=palette.bg
        ).pack(anchor="center")

        tk.Label(
            win,
            text=title.upper(),
            font=("Helvetica", 12, "bold"),
            bg=palette.bg,
            fg=palette.text
        ).pack()

        tk.Label(
            win,
            text="Enter your secure PIN",
            font=("Helvetica", 9),
            bg=palette.bg,
            fg="#7f8c8d"
        ).pack(pady=(0, 20))

        pass_var = tk.StringVar()

        entry = tk.Entry(
            win,
            textvariable=pass_var,
            font=("Helvetica", 18),
            show="●",
            justify="center",
            bd=0,
            bg=palette.win95,
            width=15
        )
        entry.pack(ipady=10)
        entry.focus_set()

        tk.Frame(win, height=2, width=200, bg=palette.text).pack(pady=(0, 20))

        error_lbl = tk.Label(
            win,
            text="",
            font=("Helvetica", 8),
            bg=palette.bg,
            fg=palette.danger
        )
        error_lbl.pack()

        def verify():
            pin = pass_var.get()
            if role == "Admin" and pin in ["admin123", "a123", "123"]:
                win.destroy()
                play("PopOpen.wav"); start_order_type(window, user_role="Admin")
            elif role == "Kitchen" and pin in ["kitchen123", "k123", "123"]:
                win.destroy()
                start_kitchen_panel(window)
            else:
                pass_var.set("")
                error_lbl.config(text="Incorrect PIN. Please try again.")

        btn_row = tk.Frame(win, bg=palette.bg)
        btn_row.pack(side="bottom", fill="x", pady=20)

        tk.Button(
            btn_row,
            text="CANCEL",
            font=("Helvetica", 9, "bold"),
            bg=palette.bg,
            fg=palette.text,
            relief="flat",
            command=win.destroy,
            cursor="hand2"
        ).pack(side="left", padx=30)

        tk.Button(
            btn_row,
            text="LOGIN",
            font=("Helvetica", 9, "bold"),
            bg=palette.text,
            fg="white",
            relief="flat",
            width=12,
            height=2,
            command=verify,
            cursor="hand2"
        ).pack(side="right", padx=30)

        win.bind("<Return>", lambda e: verify())

    def open_admin_panel_direct():
        win = tk.Toplevel(window)
        win.title("Admin Panel Access")
        win.geometry("320x400")
        win.configure(bg=palette.bg)
        win.resizable(False, False)
        win.transient(window)
        win.grab_set()

        x = window.winfo_x() + window.winfo_width() // 2 - 160
        y = window.winfo_y() + window.winfo_height() // 2 - 200
        win.geometry(f"+{x}+{y}")

        icon_frame = tk.Frame(win, bg=palette.bg)
        icon_frame.pack(fill="x", pady=(30, 10))

        tk.Label(
            icon_frame,
            text="🖥️",
            font=("Arial", 30),
            bg=palette.bg
        ).pack(anchor="center")

        tk.Label(
            win,
            text="ADMIN PANEL",
            font=("Helvetica", 12, "bold"),
            bg=palette.bg,
            fg=palette.text
        ).pack()

        tk.Label(
            win,
            text="Enter your secure PIN",
            font=("Helvetica", 9),
            bg=palette.bg,
            fg="#7f8c8d"
        ).pack(pady=(0, 20))

        pass_var = tk.StringVar()

        entry = tk.Entry(
            win,
            textvariable=pass_var,
            font=("Helvetica", 18),
            show="●",
            justify="center",
            bd=0,
            bg=palette.win95,
            width=15
        )
        entry.pack(ipady=10)
        entry.focus_set()

        tk.Frame(win, height=2, width=200, bg=palette.text).pack(pady=(0, 20))

        err = tk.Label(
            win,
            text="",
            font=("Helvetica", 8),
            bg=palette.bg,
            fg=palette.danger
        )
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

        tk.Button(
            btn_row,
            text="CANCEL",
            font=("Helvetica", 9, "bold"),
            bg=palette.bg,
            fg=palette.text,
            relief="flat",
            command=win.destroy,
            cursor="hand2"
        ).pack(side="left", padx=30)

        tk.Button(
            btn_row,
            text="LOGIN",
            font=("Helvetica", 9, "bold"),
            bg=palette.text,
            fg="white",
            relief="flat",
            width=12,
            height=2,
            command=verify,
            cursor="hand2"
        ).pack(side="right", padx=30)

        win.bind("<Return>", lambda e: verify())

