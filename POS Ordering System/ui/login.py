import tkinter as tk
from tkinter import messagebox
from ui.dashboard import start_dashboard

# Credentials moved here
ADMIN_USER = "admin"
ADMIN_PASS = "123"


def start_login():
    window = tk.Tk()
    window.title("Fast Food POS System")
    window.geometry("1100x650")
    window.configure(bg="#f4f4f4")

    login_frame = tk.Frame(window, bg="white", padx=40, pady=40)
    login_frame.pack(expand=True)

    tk.Label(login_frame, text="ADMIN LOGIN", font=("Arial", 18, "bold"), bg="white").pack(pady=10)

    user_entry = tk.Entry(login_frame, font=("Arial", 12), width=25)
    user_entry.pack(pady=10, ipady=5)

    pass_entry = tk.Entry(login_frame, show="*", font=("Arial", 12), width=25)
    pass_entry.pack(pady=10, ipady=5)

    def attempt_login():
        if user_entry.get() == ADMIN_USER and pass_entry.get() == ADMIN_PASS:
            login_frame.destroy()
            start_dashboard(window)
        else:
            messagebox.showerror("Error", "Invalid Username or Password")

    tk.Button(login_frame, text="LOGIN", font=("Arial", 12, "bold"),
              bg="#27ae60", fg="white", width=20, command=attempt_login).pack(pady=20)

    window.mainloop()