import datetime
import os
import random
import string


def generate_receipt_file(cash, change, invoice_no, total, summary, mode="counter"):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    receipt_dir = os.path.join(base, "receipts")
    os.makedirs(receipt_dir, exist_ok=True)

    file_path = os.path.join(receipt_dir, f"receipt_{invoice_no}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("FAST FOOD ORPOSS\n")
        f.write(f"MODE: {mode.upper()}\n")
        f.write(f"INVOICE: {invoice_no}\n")
        f.write(f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 35 + "\n")
        for item, data in summary.items():
            line_total = data["qty"] * data["price"]
            f.write(f"{item:<15} {data['qty']}x  ₱{line_total:>8.2f}\n")
        f.write("-" * 35 + "\n")
        f.write(f"TOTAL:   ₱{total:>9.2f}\n")
        f.write(f"CASH:    ₱{cash:>9.2f}\n")
        f.write(f"CHANGE:  ₱{change:>9.2f}\n")
        if mode == "kiosk":
            ref = "".join(random.choices(string.ascii_uppercase, k=8))
            f.write(f"\nPAYMENT VIA E-WALLET\nREF: {ref}\n")
        f.write("\nTHANK YOU!\n")
