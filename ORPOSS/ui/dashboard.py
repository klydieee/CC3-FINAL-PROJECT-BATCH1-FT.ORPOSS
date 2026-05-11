import tkinter as tk
from tkinter import messagebox
import datetime
import os
import sys

# Project-specific Imports
from data.inventory import inventory
from utils.helper import peso
from utils.receipt_generator import generate_receipt_file
from ui.receipt_popup import show_receipt_popup
from ui.order_review import show_order_review
from ui.admin_panel import start_admin_panel


def start_dashboard(window, user_role="Client"):
    # Clear previous widgets
    for widget in window.winfo_children():
        widget.destroy()

    # --- FULLSCREEN CONFIGURATION ---
    window.attributes('-fullscreen', True) # Set to full screen

    # Allow user to exit fullscreen with the Escape Key
    window.bind("<Escape>", lambda event: window.attributes("-fullscreen", False))

    # Optional: Toggle fullscreen with F11
    window.bind("<F11>", lambda event: window.attributes("-fullscreen", not window.attributes("-fullscreen")))

    # --- UI Configuration ---
    BG_COLOR = "#f8f9fa"
    TEXT_COLOR = "#2c3e50"
    PRIMARY_COLOR = "#e67e22"
    SECONDARY_COLOR = "#2ecc71"

    def on_closing():
        if messagebox.askokcancel("Quit", "Exit system?"):
            window.destroy()
            sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    # State Variables
    cart = {}
    buttons = {}
    cash_var = tk.StringVar(value="₱")

    # Formatting for Cash Entry
    def format_cash(*args):
        val = cash_var.get()
        digits = "".join(filter(str.isdigit, val))
        cash_var.set(f"₱{digits}" if digits else "₱")

    cash_var.trace_add("write", format_cash)

    def get_cart_total():
        return sum(inventory[name]['price'] * qty for name, qty in cart.items())

    def empty_cart():
        if not cart: return
        if messagebox.askyesno("Confirm Clear", "Clear all items from your tray?"):
            for name, qty in cart.items():
                inventory[name]['stock'] += qty
            cart.clear()
            update_ui()

    # --- UI Logic ---
    def update_ui():
        # Update Tray Items
        for widget in cart_scroll_frame.winfo_children():
            widget.destroy()

        if not cart:
            tk.Label(cart_scroll_frame, text="Your tray is empty", font=("Segoe UI", 11, "italic"),
                     fg="#95a5a6", bg="white", pady=60).pack()

        for name, qty in cart.items():
            row = tk.Frame(cart_scroll_frame, bg="white", pady=12)
            row.pack(fill="x", padx=15, pady=2)

            info_f = tk.Frame(row, bg="white")
            info_f.pack(side="left", fill="x", expand=True)
            tk.Label(info_f, text=name.upper(), font=("Segoe UI", 10, "bold"), bg="white", fg=TEXT_COLOR).pack(
                side="top", anchor="w")
            tk.Label(info_f, text=f"{qty}x - {peso(inventory[name]['price'] * qty)}",
                     font=("Segoe UI", 9), fg=PRIMARY_COLOR, bg="white").pack(side="top", anchor="w")

            btn_f = tk.Frame(row, bg="white")
            btn_f.pack(side="right")
            tk.Button(btn_f, text="-", width=2, bg="#e74c3c", fg="white", relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, -1)).pack(side="left", padx=2)
            tk.Label(btn_f, text=str(qty), font=("Segoe UI", 10, "bold"), bg="white", width=3).pack(side="left")
            tk.Button(btn_f, text="+", width=2, bg=SECONDARY_COLOR, fg="white", relief="flat",
                      font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, 1)).pack(side="left", padx=2)

        cart_scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # Update Totals and Item Cards
        total_lbl.config(text=f"{peso(get_cart_total())}")
        for name, btn in buttons.items():
            s = inventory[name]['stock']
            if s <= 0:
                btn.config(state="disabled", bg="#eee", text=f"{name}\nSOLD OUT", fg="#999")
            else:
                btn.config(state="normal", bg="white", text=f"{name}\n{peso(inventory[name]['price'])}")

    def adjust_qty(name, amt):
        if amt > 0 and inventory[name]['stock'] > 0:
            cart[name] = cart.get(name, 0) + 1
            inventory[name]['stock'] -= 1
        elif amt < 0 and name in cart:
            cart[name] -= 1
            inventory[name]['stock'] += 1
            if cart[name] <= 0: del cart[name]
        update_ui()

    # --- MAIN LAYOUT ---

    # 1. SIDEBAR
    sidebar = tk.Frame(window, bg=TEXT_COLOR, width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="Customer\nWindow", fg="white", bg=TEXT_COLOR,
             font=("Segoe UI", 16, "bold"), justify="center").pack(pady=50)

    if user_role == "Admin":
        tk.Button(sidebar, text="ADMIN PANEL", bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
                  relief="flat",
                  command=lambda: start_admin_panel(window, lambda: start_dashboard(window, user_role))).pack(
            side="bottom", fill="x", pady=20, padx=15)

    # 2. MENU AREA
    menu_area = tk.Frame(window, bg=BG_COLOR)
    menu_area.pack(side="left", fill="both", expand=True)
    tk.Label(menu_area, text="SELECT YOUR MEAL", font=("Segoe UI", 24, "bold"),
             bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=(50, 30), anchor="w", padx=60)

    grid_container = tk.Canvas(menu_area, bg=BG_COLOR, highlightthickness=0)
    grid_container.pack(fill="both", expand=True, padx=50)

    grid = tk.Frame(grid_container, bg=BG_COLOR)
    grid_container.create_window((0, 0), window=grid, anchor="nw")

    r, c = 0, 0
    for name in inventory:
        card = tk.Button(grid, text="", width=26, height=11, relief="flat", font=("Segoe UI", 12, "bold"),
                         bg="white", fg=TEXT_COLOR, bd=0, cursor="hand2", highlightthickness=1,
                         highlightbackground="#ecf0f1")
        card.config(command=lambda n=name: adjust_qty(n, 1))
        card.grid(row=r, column=c, padx=20, pady=20)
        buttons[name] = card
        c += 1
        if c > 2: c, r = 0, r + 1

    # 3. TRAY PANEL
    tray_panel = tk.Frame(window, bg="white", width=450)
    tray_panel.pack(side="right", fill="y")
    tray_panel.pack_propagate(False)

    header = tk.Frame(tray_panel, bg="white", pady=25)
    header.pack(fill="x")
    tk.Label(header, text="YOUR TRAY", font=("Segoe UI", 16, "bold"), bg="white").pack(side="left", padx=30)
    tk.Button(header, text="EMPTY", bg="#e74c3c", fg="white", font=("Segoe UI", 8, "bold"),
              relief="flat", padx=15, command=empty_cart).pack(side="right", padx=30)

    canvas_f = tk.Frame(tray_panel, bg="white")
    canvas_f.pack(fill="both", expand=True)
    canvas = tk.Canvas(canvas_f, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_f, orient="vertical", command=canvas.yview)
    cart_scroll_frame = tk.Frame(canvas, bg="white")

    canvas_win = canvas.create_window((0, 0), window=cart_scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

    # 4. CHECKOUT FOOTER
    checkout_f = tk.Frame(tray_panel, bg="#fdfdfd", pady=30, padx=30, bd=1, relief="solid")
    checkout_f.pack(side="bottom", fill="x")

    total_f = tk.Frame(checkout_f, bg="#fdfdfd")
    total_f.pack(fill="x", pady=(0, 20))
    tk.Label(total_f, text="GRAND TOTAL", font=("Segoe UI", 11, "bold"), bg="#fdfdfd", fg="#7f8c8d").pack(side="left")
    total_lbl = tk.Label(total_f, text="₱0.00", font=("Segoe UI", 26, "bold"), fg=PRIMARY_COLOR, bg="#fdfdfd")
    total_lbl.pack(side="right")

    tk.Entry(checkout_f, textvariable=cash_var, justify="center", font=("Segoe UI", 24), bd=0, bg="#f1f2f6").pack(
        fill="x", pady=(0, 20), ipady=12)

    # --- FIXED CHECKOUT LOGIC ---
    def handle_checkout():
        total = get_cart_total()
        if not cart: return

        try:
            # CAPTURE DATA SNAPSHOT BEFORE ANY UI RESETS
            raw_val = cash_var.get().replace("₱", "").strip()
            current_cash = float(raw_val) if raw_val else 0.0

            if current_cash < total:
                messagebox.showerror("Denied", f"Cash is less than the total {peso(total)}")
                return

            # Snapshots of the cart items to ensure receipt has data
            summary = {name: {"qty": q, "price": inventory[name]['price']} for name, q in cart.items()}

            def finalize(mode):
                inv_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                change = current_cash - total

                # Pass the snapshots, not the live cart
                generate_receipt_file(current_cash, change, inv_no, total, summary, mode)
                show_receipt_popup(window, current_cash, change, inv_no, total, summary, mode)

                # Reset only after success
                cart.clear()
                cash_var.set("₱")
                update_ui()

            show_order_review(window, current_cash, total, summary, finalize)

        except ValueError:
            messagebox.showerror("Error", "Invalid cash amount.")

    tk.Button(checkout_f, text="PLACE ORDER", bg=SECONDARY_COLOR, fg="white", font=("Segoe UI", 16, "bold"),
              height=2, relief="flat", command=handle_checkout).pack(fill="x")

    # Quick Cash Buttons
    qs_f = tk.Frame(checkout_f, bg="#fdfdfd")
    qs_f.pack(fill="x", pady=(20, 0))
    for amt in [100, 200, 500, 1000]:
        tk.Button(qs_f, text=f"₱{amt}", font=("Segoe UI", 10, "bold"), bg="white", relief="flat",
                  highlightthickness=1, highlightbackground="#dcdde1",
                  command=lambda a=amt: cash_var.set(f"₱{a}")).pack(side="left", padx=3, expand=True, fill="x")

    update_ui()