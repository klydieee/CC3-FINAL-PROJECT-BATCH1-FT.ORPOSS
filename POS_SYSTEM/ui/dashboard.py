#ui/dashboard.py
import tkinter as tk
from tkinter import messagebox
import datetime

#Import modules from local packages
from data.inventory import inventory
from ui.receipt_popup import show_receipt_popup
from utils.receipt_generator import generate_receipt_file
from utils.helper import peso

def start_dashboard(window):
    #Root window configuration
    window.title("Fast Food POS System")
    window.configure(bg="#f8f9fa")

    #Main container frame
    dashboard_frame = tk.Frame(window, bg="#f8f9fa")
    dashboard_frame.pack(fill="both", expand=True)

    #Application state variables
    cart = []
    state = {"total": 0.0}
    buttons = {}

    def update_cart_ui():
        #Reset listbox content and refresh total price display
        listbox.delete(0, tk.END)
        for item, price in cart:
            listbox.insert(tk.END, f" {item:<20} {peso(price):>10}")
        total_label.config(text=f"TOTAL: {peso(state['total'])}")

    def refresh_menu_buttons():
        #Synchronize button appearance with current inventory stock levels
        for name, btn in buttons.items():
            stock = inventory[name]['stock']
            btn.config(
                text=f"{name}\n{peso(inventory[name]['price'])}\nStock: {stock}",
                state="normal" if stock > 0 else "disabled",
                bg="white" if stock > 0 else "#dfe6e9"
            )

    def add_item(name):
        #Transactional logic for adding items and decrementing stock
        if inventory[name]["stock"] <= 0:
            messagebox.showwarning("Out of Stock", f"{name} is unavailable")
            return
        cart.append((name, inventory[name]["price"]))
        state["total"] += inventory[name]["price"]
        inventory[name]["stock"] -= 1
        update_cart_ui()
        refresh_menu_buttons()

    def clear_cart():
        #Revert stock changes and clear session data
        for item_name, _ in cart:
            inventory[item_name]["stock"] += 1
        cart.clear()
        state["total"] = 0.0
        update_cart_ui()
        refresh_menu_buttons()

    def checkout():
        #Payment validation and receipt generation sequence
        if not cart:
            messagebox.showwarning("Empty Cart", "Please add items first!")
            return

        try:
            cash = float(cash_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid cash amount")
            return

        if cash < state["total"]:
            messagebox.showerror("Error", "Insufficient Cash")
            return

        change = cash - state["total"]
        invoice_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        #Aggregate items into a quantity-based summary
        summary = {}
        for item, price in cart:
            if item in summary:
                summary[item]["qty"] += 1
            else:
                summary[item] = {"qty": 1, "price": price}

        #String formatting for the modal receipt display
        receipt_text = (f"INVOICE #: {invoice_no}\n" + "=" * 40 + "\n"
                        f"{'ITEM':<20}{'QTY':<6}{'PRICE':<10}\n" + "-" * 40 + "\n")

        for item, data in summary.items():
            receipt_text += f"{item:<20}{data['qty']:<6}{peso(data['qty'] * data['price']):<10}\n"

        receipt_text += ("-" * 40 + f"\nTOTAL: {peso(state['total']):>25}\n"
                        f"CASH:  {peso(cash):>25}\nCHANGE: {peso(change):>25}\n" + "=" * 40)

        #Trigger file IO and UI popup
        generate_receipt_file(cash, change, invoice_no, state["total"], summary)
        show_receipt_popup(window, receipt_text)

        #Reset session after successful transaction
        cart.clear()
        state["total"] = 0.0
        cash_entry.delete(0, tk.END)
        update_cart_ui()

    #Layout for item selection grid
    menu_frame = tk.Frame(dashboard_frame, bg="#f8f9fa")
    menu_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

    #Layout for sidebar cart and controls
    cart_frame = tk.Frame(dashboard_frame, bg="white", width=380, bd=1, relief="solid")
    cart_frame.pack(side="right", fill="y", padx=10, pady=10)
    cart_frame.pack_propagate(False)

    listbox = tk.Listbox(cart_frame, width=40, height=18, font=("Courier", 10), bd=0)
    listbox.pack(pady=10, padx=10)

    total_label = tk.Label(cart_frame, text="TOTAL: ₱0.00", font=("Arial", 16, "bold"), bg="white", fg="#27ae60")
    total_label.pack(pady=10)

    cash_entry = tk.Entry(cart_frame, font=("Arial", 14), justify="center", width=15)
    cash_entry.insert(0, "0")
    cash_entry.pack(pady=5)

    tk.Button(cart_frame, text="PROCESS CHECKOUT", bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
              height=2, width=30, command=checkout).pack(pady=10)

    tk.Button(cart_frame, text="CLEAR ORDER", bg="#e74c3c", fg="white", width=30, command=clear_cart).pack()

    #Dynamic button grid generation based on inventory keys
    grid_frame = tk.Frame(menu_frame, bg="#f8f9fa")
    grid_frame.pack()

    r, c = 0, 0
    for name in inventory:
        btn = tk.Button(grid_frame, text="", width=18, height=6, font=("Arial", 9, "bold"),
                        command=lambda n=name: add_item(n))
        btn.grid(row=r, column=c, padx=10, pady=10)
        buttons[name] = btn
        c += 1
        if c > 2: #Grid boundary: 3 columns
            c = 0
            r += 1

    #Initial state sync
    refresh_menu_buttons()
    update_cart_ui()