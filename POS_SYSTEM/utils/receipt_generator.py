import datetime
import os


def generate_receipt_file(cash, change, invoice_no, total, summary):
    if not os.path.exists("receipts"):
        os.makedirs("receipts")

    file_path = f"receipts/receipt_{invoice_no}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("====== FAST FOOD RECEIPT ======\n")
        f.write(f"INVOICE #: {invoice_no}\n")
        f.write(str(datetime.datetime.now()) + "\n\n")
        f.write(f"{'ITEM#':<8}{'ITEM':<15}{'QTY':<8}{'PRICE':<10}\n")
        f.write("-" * 45 + "\n")

        for i, (item, data) in enumerate(summary.items(), 1):
            total_price = data["qty"] * data["price"]
            f.write(f"{i:<8}{item:<15}{data['qty']:<8}₱{total_price:<10}\n")

        f.write("-" * 45 + "\n")
        f.write(f"TOTAL: ₱{total}\n")
        f.write(f"CASH: ₱{cash}\n")
        f.write(f"CHANGE: ₱{change}\n\n")
        f.write("PROOF OF BILLING\nALL RIGHTS RESERVED\n")