import tkinter as tk
from tkinter import messagebox
from ui.dashboard import start_dashboard


def start_login(window):
    # Clear previous widgets
    for widget in window.winfo_children():
        widget.destroy()

    window.configure(bg="#ffffff")

    # --- Landing Page Content ---
    main_container = tk.Frame(window, bg="white")
    main_container.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        main_container,
        text="ORPOSS",
        font=("Helvetica", 52, "bold"),
        bg="white",
        fg="#2c3e50"
    ).pack()

    tk.Label(
        main_container,
        text="Fresh Food. Fast Service.",
        font=("Helvetica", 14),
        bg="white",
        fg="#95a5a6"
    ).pack(pady=(0, 50))

    start_btn = tk.Button(
        main_container,
        text="START ORDER  >",
        font=("Helvetica", 18, "bold"),
        bg="#27ae60",
        fg="white",
        activebackground="#2ecc71",
        activeforeground="white",
        relief="flat",
        padx=50,
        pady=20,
        cursor="hand2",
        command=lambda: start_dashboard(window, user_role="Client")
    )
    start_btn.pack()

    # --- CUSTOM PROFESSIONAL ADMIN LOGIN ---
    def open_custom_admin_login():
        login_win = tk.Toplevel(window)
        login_win.title("Security Check")
        login_win.geometry("320x400")
        login_win.configure(bg="white")
        login_win.resizable(False, False)

        # Modal behavior
        login_win.transient(window)
        login_win.grab_set()

        # Center the popup relative to main window
        x = window.winfo_x() + (window.winfo_width() // 2) - 160
        y = window.winfo_y() + (window.winfo_height() // 2) - 200
        login_win.geometry(f"+{x}+{y}")

        # Icon and Title
        tk.Label(login_win, text="🔒", font=("Arial", 30), bg="white").pack(pady=(30, 10))
        tk.Label(login_win, text="ADMIN ACCESS", font=("Helvetica", 12, "bold"), bg="white", fg="#2c3e50").pack()
        tk.Label(login_win, text="Please enter your secure PIN", font=("Helvetica", 9), bg="white", fg="#7f8c8d").pack(
            pady=(0, 20))

        # Password Entry Styled
        pass_var = tk.StringVar()
        pass_entry = tk.Entry(
            login_win,
            textvariable=pass_var,
            font=("Helvetica", 18),
            show="●",
            justify="center",
            bd=0,
            bg="#f5f6fa",
            width=15
        )
        pass_entry.pack(ipady=10)
        pass_entry.focus_set()

        # Underline accent
        tk.Frame(login_win, height=2, width=200, bg="#2c3e50").pack(pady=(0, 30))

        def verify():
            if pass_var.get() == "admin123":
                login_win.destroy()
                start_dashboard(window, user_role="Admin")
            else:
                pass_var.set("")  # Clear entry
                error_lbl.config(text="Incorrect Password. Try again.")

        error_lbl = tk.Label(login_win, text="", font=("Helvetica", 8), bg="white", fg="#e74c3c")
        error_lbl.pack()

        # Action Buttons
        btn_frame = tk.Frame(login_win, bg="white")
        btn_frame.pack(side="bottom", fill="x", pady=20)

        tk.Button(
            btn_frame, text="CANCEL", font=("Helvetica", 9, "bold"), bg="white", fg="#95a5a6",
            relief="flat", command=login_win.destroy, cursor="hand2"
        ).pack(side="left", padx=30)

        tk.Button(
            btn_frame, text="LOGIN", font=("Helvetica", 9, "bold"), bg="#2c3e50", fg="white",
            relief="flat", width=12, height=2, command=verify, cursor="hand2"
        ).pack(side="right", padx=30)

        # Bind Enter key
        login_win.bind('<Return>', lambda e: verify())

    # Mini Admin Access Button (Bottom Right)
    admin_btn = tk.Button(
        window,
        text="ADMIN SETTINGS",
        font=("Helvetica", 8, "bold"),
        bg="#f5f6fa",
        fg="#bdc3c7",
        activebackground="#f5f6fa",
        activeforeground="#2c3e50",
        relief="flat",
        padx=10,
        pady=5,
        cursor="hand2",
        command=open_custom_admin_login
    )
    admin_btn.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)