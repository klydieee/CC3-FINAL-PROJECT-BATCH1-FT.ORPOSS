import customtkinter as ctk
from ui.login import start_login

def main():
    root = ctk.CTk()
    root.title("ORPOSS — Ordering & Point of Sales System")

    width, height = 1200, 700
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{width}x{height}+{(sw-width)//2}+{(sh-height)//2}")

    start_login(root)
    root.mainloop()

if __name__ == "__main__":
    main()
