import tkinter as tk

def show_receipt_popup(parent, receipt_text):
    popup = tk.Toplevel(parent)
    popup.title("Transaction Receipt")
    popup.geometry("500x450")
    popup.configure(bg="white")

    tk.Label(
        popup,
        text="TRANSACTION SUCCESS",
        font=("Arial", 14, "bold"),
        bg="white",
        fg="#27ae60"
    ).pack(pady=10)

    text_area = tk.Text(popup, font=("Courier New", 11))
    text_area.pack(fill="both", expand=True, padx=10, pady=10)

    text_area.insert("1.0", receipt_text)
    text_area.config(state="disabled")