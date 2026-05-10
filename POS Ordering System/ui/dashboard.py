import tkinter as tk
from tkinter import messagebox
import datetime

from data.inventory import inventory
from ui.receipt_popup import show_receipt_popup
from utils.receipt_generator import generate_receipt_file


def start_dashboard(window):
    dashboard_frame = tk.Frame(window, bg="#f4f4f4")
    dashboard_frame.pack(fill="both", expand=True)

    cart = []
    state = {"total": 0}

    def update_cart_ui():
        listbox.delete(0, tk.END)
        for item, price in cart:
            listbox.insert(tk.END, f"{item} - ₱{price}")
        total_label.config(text=f"TOTAL: ₱{state['total']}")

    def refresh_menu_buttons():
        for name, btn in buttons.items():
            btn.config(text=f"{name}\n₱{inventory[name]['price']}\nStock: {inventory[name]['stock']}")

    def add_item(name):
        if inventory[name]["stock"] <= 0:
            messagebox.showwarning("Out of Stock", f"{name} is unavailable")
            return
        cart.append((name, inventory[name]["price"]))
        state["total"] += inventory[name]["price"]
        inventory[name]["stock"] -= 1
        update_cart_ui()
        refresh_menu_buttons()

    def clear_cart():
        cart.clear()
        state["total"] = 0
        update_cart_ui()

    def checkout():
        cash_val = cash_entry.get()
        if not cash_val.isdigit():
            messagebox.showerror("Error", "Enter valid cash")
            return

        cash = int(cash_val)
        if cash < state["total"]:
            messagebox.showerror("Error", "Not enough cash")
            return

        change = cash - state["total"]
        invoice_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        summary = {}
        for item, price in cart:
            if item in summary:
                summary[item]["qty"] += 1
            else:
                summary[item] = {"qty": 1, "price": price}

        lines = "".join([f"{i + 1:<8}{item:<15}{d['qty']:<8}₱{d['qty'] * d['price']:<10}\n"
                         for i, (item, d) in enumerate(summary.items())])

        receipt_text = (f"INVOICE #: {invoice_no}\n\n"
                        f"{'ITEM#':<8}{'ITEM':<15}{'QTY':<8}{'PRICE':<10}\n"
                        f"{'-' * 45}\n{lines}{'-' * 45}\n"
                        f"TOTAL: ₱{state['total']}\nCASH: ₱{cash}\nCHANGE: ₱{change}")

        generate_receipt_file(cash, change, invoice_no, state["total"], summary)
        show_receipt_popup(window, receipt_text)
        clear_cart()

    # UI construction...
    menu_frame = tk.Frame(dashboard_frame, bg="#f4f4f4")
    menu_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

    grid_frame = tk.Frame(menu_frame, bg="#f4f4f4")
    grid_frame.pack()

    cart_frame = tk.Frame(dashboard_frame, bg="white", width=350)
    cart_frame.pack(side="right", fill="y", padx=15, pady=15)

    listbox = tk.Listbox(cart_frame, width=35, height=18, font=("Arial", 11))
    listbox.pack(pady=10)

    total_label = tk.Label(cart_frame, text="TOTAL: ₱0", font=("Arial", 14, "bold"), bg="white")
    total_label.pack(pady=10)

    cash_entry = tk.Entry(cart_frame, font=("Arial", 12))
    cash_entry.pack(pady=10)

    tk.Button(cart_frame, text="CHECKOUT", bg="#27ae60", fg="white", command=checkout).pack(pady=5)
    tk.Button(cart_frame, text="CLEAR", bg="#e74c3c", fg="white", command=clear_cart).pack(pady=5)

    buttons = {}
    r, c = 0, 0
    for name in inventory:
        btn = tk.Button(grid_frame, text="", width=18, height=6, command=lambda n=name: add_item(n))
        btn.grid(row=r, column=c, padx=10, pady=10)
        buttons[name] = btn
        c += 1
        if c > 2: c = 0; r += 1

    refresh_menu_buttons()