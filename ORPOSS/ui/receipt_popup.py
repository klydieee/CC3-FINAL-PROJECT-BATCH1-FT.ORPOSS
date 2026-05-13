import tkinter as tk
from utils.helper import peso
import random
import string
import qrcode
from PIL import ImageTk, Image


def show_receipt_popup(parent_window, cash, change, invoice_no, total, summary, mode="counter", on_done=None):
    # Create popup window
    popup = tk.Toplevel(parent_window)
    popup.title("E-Receipt")
    popup.geometry("380x800")
    popup.configure(bg="white")

    # Force the popup to stay on top
    popup.transient(parent_window)
    popup.grab_set()

    # Header
    tk.Label(popup, text="FAST FOOD ORPOSS", font=("Courier", 14, "bold"), bg="white").pack(pady=(20, 5))

    # Display Mode
    mode_color = "#3498db" if mode.lower() == "kiosk" else "#2c3e50"
    tk.Label(popup, text=f"MODE: {mode.upper()}", font=("Courier", 10, "bold"),
             bg="white", fg=mode_color).pack()

    tk.Label(popup, text=f"Invoice: {invoice_no}", font=("Courier", 9), bg="white").pack()
    tk.Label(popup, text="-" * 40, bg="white").pack()

    # Itemized List Frame
    content_frame = tk.Frame(popup, bg="white")
    content_frame.pack(fill="x", padx=30)

    header_row = tk.Frame(content_frame, bg="white")
    header_row.pack(fill="x")
    tk.Label(header_row, text="QTY  ITEM", font=("Courier", 9, "bold"), bg="white").pack(side="left")
    tk.Label(header_row, text="PRICE", font=("Courier", 9, "bold"), bg="white").pack(side="right")

    for item, data in summary.items():
        row = tk.Frame(content_frame, bg="white")
        row.pack(fill="x", pady=2)
        qty_name = f"{data['qty']}x {item[:18]}"
        tk.Label(row, text=qty_name, font=("Courier", 10), bg="white").pack(side="left")
        item_total = data['qty'] * data['price']
        tk.Label(row, text=peso(item_total), font=("Courier", 10), bg="white").pack(side="right")

    tk.Label(popup, text="-" * 40, bg="white").pack(pady=5)

    # Totals Section
    footer_frame = tk.Frame(popup, bg="white")
    footer_frame.pack(fill="x", padx=30, pady=5)

    # Always show Total
    tk.Label(footer_frame, text=f"TOTAL: {peso(total)}", font=("Courier", 12, "bold"), bg="white").pack(anchor="e")

    # Only show Cash and Change for Counter/Over-the-counter mode
    if mode.lower() == "counter":
        tk.Label(footer_frame, text=f"CASH: {peso(cash)}", font=("Courier", 10), bg="white").pack(anchor="e")
        tk.Label(footer_frame, text=f"CHANGE: {peso(change)}", font=("Courier", 11, "bold"), bg="white").pack(
            anchor="e")

    # QR Code Section (For Kiosk/E-Wallet)
    if mode.lower() == "kiosk":
        ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        tk.Label(popup, text="-" * 40, bg="white").pack(pady=5)

        try:
            qr_data = f"ORPOSS|{invoice_no}|{total}|{ref_code}"
            qr_gen = qrcode.QRCode(version=1, box_size=4, border=2)
            qr_gen.add_data(qr_data)
            qr_gen.make(fit=True)

            qr_img = qr_gen.make_image(fill_color="black", back_color="white")
            tk_qr_img = ImageTk.PhotoImage(qr_img)

            qr_label = tk.Label(popup, image=tk_qr_img, bg="white")
            qr_label.image = tk_qr_img
            qr_label.pack(pady=10)

            tk.Label(popup, text=f"REF: {ref_code}", font=("Courier", 11, "bold"), bg="white").pack()
            tk.Label(popup, text="Scan with GCash / Maya", font=("Courier", 8), bg="white").pack()

        except Exception as e:
            print(f"QR Generation Error: {e}")
            tk.Label(popup, text="[ QR GENERATION ERROR ]", font=("Courier", 8), fg="red", bg="white").pack()

    # Footer
    tk.Label(popup, text="\nTHANK YOU!", font=("Courier", 9, "italic"), bg="white").pack(pady=10)

    def handle_done():
        popup.destroy()
        if on_done:
            on_done()

    tk.Button(popup, text="DONE", command=handle_done,
              bg="#2c3e50", fg="white", font=("Segoe UI", 10, "bold"),
              relief="flat", width=20, height=2, cursor="hand2").pack(pady=20)