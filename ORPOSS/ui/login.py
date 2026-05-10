import tkinter as tk
from tkinter import messagebox

USERS = {
    "admin": {"pass": "123", "role": "Admin"},
    "teller1": {"pass": "456", "role": "Teller"}
}

def start_login():
    window = tk.Tk()
    window.title("Fast Food ORPOSS")
    window.geometry("1100x650")
    window.configure(bg="#f4f4f4")

    login_frame = tk.Frame(window, bg="white", padx=40, pady=40)
    login_frame.pack(expand=True)

    tk.Label(login_frame, text="USER LOGIN", font=("Arial", 18, "bold"), bg="white").pack(pady=10)

    user_entry = tk.Entry(login_frame, font=("Arial", 12), width=25)
    user_entry.insert(0, "Username") # Placeholder
    user_entry.pack(pady=10, ipady=5)

    pass_entry = tk.Entry(login_frame, show="*", font=("Arial", 12), width=25)
    pass_entry.pack(pady=10, ipady=5)

    def attempt_login():
        username = user_entry.get()
        password = pass_entry.get()

        if username in USERS and USERS[username]["pass"] == password:
            role = USERS[username]["role"]
            
            # 1. Kill the login window first
            window.destroy() 
            
            # 2. Start the MainSystem only AFTER login is dead
            from main import MainSystem
            app = MainSystem(user_role=role)
            app.mainloop()
        else:
            messagebox.showerror("Error", "Invalid Credentials")

    tk.Button(login_frame, text="LOGIN", font=("Arial", 12, "bold"),
              bg="#27ae60", fg="white", width=20, command=attempt_login).pack(pady=20)

    window.mainloop()