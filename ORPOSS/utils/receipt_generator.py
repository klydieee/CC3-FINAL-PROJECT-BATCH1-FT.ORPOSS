import datetime
import os
import random
import string

def generate_receipt_file(cash, change, invoice_no, total, summary, mode="counter"):
    if not os.path.exists("receipts"):
        os.makedirs("receipts")

    file_path = f"receipts/receipt_{invoice_no}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("FAST FOOD ORPOSS\n")
        f.write(f"MODE: {mode.upper()}\n")
        f.write(f"INVOICE: {invoice_no}\n")
        f.write("-" * 35 + "\n")
        for item, data in summary.items():
            f.write(f"{item:<15} {data['qty']}x {data['price']:>8.2f}\n")
        f.write("-" * 35 + "\n")
        f.write(f"TOTAL:  {total:>20.2f}\n")
        if mode == "kiosk":
            f.write("\nPAYMENT VIA E-WALLET\nREF: " + ''.join(random.choices(string.ascii_uppercase, k=8)) + "\n")
        f.write("\nTHANK YOU!")