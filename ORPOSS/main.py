import tkinter as tk
from ui.login import start_login


def main():
    root = tk.Tk()
    root.title("Fast Food ORPOSS")

    width, height = 1100, 650
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    start_login(root)
    root.mainloop()


if __name__ == "__main__":
    main()