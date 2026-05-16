import tkinter as tk
from utils.helper import peso
from utils.palette import palette


def show_order_review(parent_window, cash, total, summary, on_confirm):
    review_win = tk.Toplevel(parent_window)
    review_win.title("Confirm Payment Method")
    review_win.geometry("450x550")
    review_win.configure(bg=palette.bg)
    review_win.grab_set()

    tk.Label(review_win, text="FINAL REVIEW", font=("Arial", 14, "bold"),
             bg=palette.bg, fg=palette.text, pady=10).pack()

    # Item List Frame
    list_frame = tk.Frame(review_win, bg="white", bd=1, relief="solid")
    list_frame.pack(fill="both", expand=True, padx=20, pady=5)

    for item, data in summary.items():
        row = tk.Frame(list_frame, bg="white")
        row.pack(fill="x", padx=10, pady=2)
        tk.Label(row, text=f"{data['qty']}x {item}", font=("Arial", 9),
                 bg="white", fg=palette.text).pack(side="left")
        tk.Label(row, text=peso(data['qty'] * data['price']), font=("Arial", 9),
                 bg="white", fg=palette.text).pack(side="right")

    # Payment Details
    details = tk.Frame(review_win, bg=palette.bg, pady=10)
    details.pack(fill="x", padx=20)

    tk.Label(details, text=f"Total: {peso(total)}", font=("Arial", 11),
             bg=palette.bg, fg=palette.text).pack(anchor="e")
    tk.Label(details, text=f"Change: {peso(cash - total)}", font=("Arial", 12, "bold"),
             fg=palette.secondary, bg=palette.bg).pack(anchor="e")

    # Options Frame
    tk.Label(review_win, text="SELECT PAYMENT MODE:", font=("Arial", 9, "bold"),
             bg=palette.bg, fg=palette.text).pack(pady=5)
    btn_frame = tk.Frame(review_win, bg=palette.bg)
    btn_frame.pack(fill="x", pady=10)

    def select_mode(mode):
        review_win.destroy()
        on_confirm(mode)  # Passes 'counter' or 'kiosk' back to dashboard

    # Option 1: Over the Counter
    tk.Button(btn_frame, text="OVER THE COUNTER\n(Cash)", bg=palette.text,
              fg="white", font=("Arial", 10), width=18, height=3, relief="flat",
              cursor="hand2", command=lambda: select_mode("counter")).pack(side="left", padx=20)

    # Option 2: Kiosk
    tk.Button(btn_frame, text="KIOSK / E-WALLET\n(QR Code)", bg=palette.primary,
              fg="white", font=("Arial", 10), width=18, height=3, relief="flat",
              cursor="hand2", command=lambda: select_mode("kiosk")).pack(side="right", padx=20)

    tk.Button(review_win, text="CANCEL / EDIT", font=("Arial", 8), bg=palette.danger,
              fg="white", relief="flat", cursor="hand2",
              command=review_win.destroy).pack(pady=10)