import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import datetime
import sys

from db.products_db import inventory
from db.orders_db import add_order
from utils.helper import peso
from utils.receipt_generator import generate_receipt_file
from ui.receipt_popup import show_receipt_popup
from ui.order_review import show_order_review
from ui.launcher import start_launcher
from ui.login import start_login
from ui.order_status_window import open_order_status_window
from utils.palette import palette


def start_dashboard(window, user_role="Client", order_type="Dine-In"):
    # Fix for NameError: local import breaks circular dependencies
    from ui.window_utils import clear_main_window
    clear_main_window(window)

    # Window configuration
    window.attributes("-fullscreen", True)
    window.bind("<Escape>", lambda e: window.attributes("-fullscreen", False))
    window.bind("<F11>", lambda e: window.attributes("-fullscreen", not window.attributes("-fullscreen")))

    def on_closing():
        if messagebox.askokcancel("Quit", "Exit the system?"):
            window.destroy()
            sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    # UI State
    cart = {}
    buttons = {}
    stock_labels = {}
    cash_var = tk.StringVar(value="₱")

    def format_cash(*_):
        val = cash_var.get()
        digits = "".join(filter(str.isdigit, val))
        cash_var.set(f"₱{digits}" if digits else "₱")

    cash_var.trace_add("write", format_cash)

    def get_total():
        return sum(inventory[n]["price"] * q for n, q in cart.items())

    # Logic helpers
    def save_inventory():
        from db.products_db import save_stock
        for name in cart:
            save_stock(name)

    def empty_cart():
        if not cart: return
        if messagebox.askyesno("Clear Tray", "Remove all items from your tray?"):
            for n, q in cart.items():
                inventory[n]["stock"] += q
            cart.clear()
            update_ui()

    def adjust_qty(name, amt):
        if amt > 0 and inventory[name]["stock"] > 0:
            cart[name] = cart.get(name, 0) + 1
            inventory[name]["stock"] -= 1
        elif amt < 0 and name in cart:
            cart[name] -= 1
            inventory[name]["stock"] += 1
            if cart[name] <= 0: del cart[name]
        update_ui()

    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    # Refresh UI elements
    def update_ui():
        for w in cart_scroll_frame.winfo_children():
            w.destroy()

        if not cart:
            tk.Label(cart_scroll_frame, text="Your tray is empty",
                     font=("Segoe UI", 11, "italic"),
                     fg="#95a5a6", bg=palette.bg, pady=60).pack()

        for name, qty in cart.items():
            row = tk.Frame(cart_scroll_frame, bg=palette.bg, pady=12)
            row.pack(fill="x", padx=15, pady=2)

            info = tk.Frame(row, bg=palette.bg)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=name.upper(), font=("Segoe UI", 10, "bold"),
                     bg=palette.bg, fg=palette.text).pack(side="top", anchor="w")
            tk.Label(info, text=f"{qty}x – {peso(inventory[name]['price'] * qty)}",
                     font=("Segoe UI", 9), fg=palette.primary, bg=palette.bg
                     ).pack(side="top", anchor="w")

            ctrl = tk.Frame(row, bg=palette.bg)
            ctrl.pack(side="right")
            tk.Button(ctrl, text="−", width=2, bg=palette.danger, fg=palette.win95,
                      relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, -1)).pack(side="left", padx=2)
            tk.Label(ctrl, text=str(qty), font=("Segoe UI", 10, "bold"),
                     bg=palette.bg, fg=palette.text, width=3).pack(side="left")
            tk.Button(ctrl, text="+", width=2, bg=palette.secondary, fg=palette.win95,
                      relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, 1)).pack(side="left", padx=2)

        total_lbl.config(text=peso(get_total()))
        for name, frame in buttons.items():
            s = inventory[name]["stock"]
            frame.configure(fg_color=palette.win95 if s > 0 else "#e0e0e0")
            lbl = stock_labels.get(name)
            if lbl: lbl.configure(text=f"QTY: {s}",
                                  text_color=palette.danger if s < 5 else palette.secondary)

    # Checkout handler
    def handle_checkout():
        total = get_total()
        if not cart:
            messagebox.showwarning("Empty Tray", "Please add items first.")
            return
        try:
            raw = cash_var.get().replace("₱", "").strip()
            cash = float(raw) if raw else 0.0
        except ValueError:
            messagebox.showerror("Error", "Invalid cash amount.")
            return

        if cash < total:
            messagebox.showerror("Insufficient", f"Cash is less than total {peso(total)}")
            return

        # REPLACE THE OLD SUMMARY LINE WITH THIS:
        summary = {}
        total_profit = 0.0
        for n, q in cart.items():
            price = inventory[n]["price"]
            cost  = inventory[n].get("cost", 0) or 0
            item_profit = (price - cost) * q
            total_profit += item_profit

            summary[n] = {
                "qty":        q,
                "price":      price,
                "cost":       cost,
                "profit":     item_profit,
                "product_id": inventory[n].get("id"),  # FK to order_items
            }

        def finalize(mode):
            inv_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            change = cash - total
            # Now passing total_profit if your generator supports it, 
            # or it's inside the summary for the generator to find.
            generate_receipt_file(cash, change, inv_no, total, summary, mode)
            add_order(inv_no, order_type, mode, total, summary, cash=cash, change_amt=change)
            cart.clear()
            cash_var.set("₱")
            save_inventory()
            start_login(window)
            show_receipt_popup(window, cash, change, inv_no, total, summary, mode)

        show_order_review(window, cash, total, summary, finalize)

    # 1. Sidebar
    sidebar = tk.Frame(window, bg=palette.text, width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="ORPOSS", fg=palette.win95, bg=palette.text, font=("Segoe UI", 18, "bold")).pack(pady=(30, 4))
    tk.Label(sidebar, text="Customer Menu", fg=palette.win95, bg=palette.text, font=("Segoe UI", 14, "italic")).pack(pady=(0, 4))

    if user_role == "Admin":
        tk.Button(sidebar, text="📺  CUSTOMER SCREEN", bg="#34495e", fg=palette.win95, font=("Segoe UI", 8, "bold"),
                  relief="flat",
                  command=lambda: open_order_status_window(window, allow_status_update=False)
                  ).pack(fill="x", padx=15, pady=(0, 8))

    # 2. Menu Grid
    menu_scroll = ctk.CTkScrollableFrame(window, fg_color=palette.bg, corner_radius=0)
    menu_scroll.pack(side="left", fill="both", expand=True)

    tk.Label(menu_scroll, text="SELECT YOUR MEAL", font=("Segoe UI", 24, "bold"),
             bg=palette.bg, fg=palette.text).pack(anchor="w", padx=60, pady=(40, 20))

    items_area = tk.Frame(menu_scroll, bg=palette.bg)
    items_area.pack(fill="both", expand=True)

    item_frames = {}

    def make_box(n):
        frame = ctk.CTkFrame(items_area, width=200, height=200, corner_radius=0,
                             border_width=2, border_color="#808080", fg_color=palette.win95)
        frame.grid_propagate(False)

        try:
            from PIL import Image
            import urllib.request, io
            image_url = inventory[n].get("image_url", "")
            if image_url.startswith("http"):
                with urllib.request.urlopen(image_url, timeout=5) as resp:
                    img_data_raw = Image.open(io.BytesIO(resp.read()))
            else:
                img_data_raw = Image.open(image_url)
            img_data = ctk.CTkImage(img_data_raw, size=(90, 90))
            ctk.CTkLabel(frame, image=img_data, text="").pack(pady=(8, 0))
        except:
            ctk.CTkLabel(frame, text="[ NO IMAGE ]", font=("Courier", 10), text_color=palette.text).pack(pady=(8, 0))

        ctk.CTkLabel(frame, text=n.upper(), font=("Courier", 13, "bold"), text_color=palette.text).pack()

        lbl_stock = ctk.CTkLabel(frame, text=f"QTY: {inventory[n]['stock']}", font=("Courier", 11),
                                 text_color=palette.danger if inventory[n]['stock'] < 5 else palette.secondary)
        lbl_stock.pack()
        stock_labels[n] = lbl_stock
        ctk.CTkLabel(frame, text=peso(inventory[n]["price"]), font=("Courier", 13), text_color=palette.teal).pack(
            pady=(0, 6))

        def on_click(e, nm=n):
            if inventory[nm]["stock"] > 0: adjust_qty(nm, 1)

        def on_enter(e, f=frame, nm=n):
            if inventory[nm]["stock"] > 0: f.configure(fg_color="#bdbdbd")

        def on_leave(e, f=frame, nm=n):
            if inventory[nm]["stock"] > 0: f.configure(fg_color=palette.win95)

        for widget in walk(frame):
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            try:
                widget.configure(cursor="hand2")
            except:
                pass

        buttons[n] = frame
        return frame

    for name in inventory: item_frames[name] = make_box(name)

    def recalculate_grid(e=None):
        for slave in items_area.grid_slaves(): slave.grid_forget()
        num_cols = max(1, items_area.winfo_width() // 224)
        for i, (name, frame) in enumerate(item_frames.items()):
            frame.grid(row=i // num_cols, column=i % num_cols, padx=12, pady=12, sticky="nsew")
        for i in range(num_cols): items_area.grid_columnconfigure(i, weight=1)

    items_area.bind("<Configure>", lambda e: items_area.after(50, recalculate_grid))

    # 3. Tray Panel
    tray = tk.Frame(window, bg=palette.bg, width=420)
    tray.pack(side="right", fill="y")
    tray.pack_propagate(False)

    hdr = tk.Frame(tray, bg=palette.bg, pady=16)
    hdr.pack(fill="x")

    title_row = tk.Frame(hdr, bg=palette.bg)
    title_row.pack(fill="x", padx=24)
    tk.Label(title_row, text="YOUR TRAY", font=("Segoe UI", 16, "bold"), bg=palette.bg, fg=palette.text).pack(
        side="left")
    tk.Button(title_row, text="EMPTY", bg=palette.danger, fg=palette.win95, font=("Segoe UI", 8, "bold"), relief="flat",
              command=empty_cart).pack(side="right")

    badge_row = tk.Frame(hdr, bg=palette.bg)
    badge_row.pack(fill="x", padx=24, pady=(6, 0))
    badge_color = palette.text if order_type == "Dine-In" else palette.primary
    tk.Label(badge_row, text=f"{'🍽️' if order_type == 'Dine-In' else '🥡'} {order_type.upper()}",
             font=("Segoe UI", 9, "bold"), bg=badge_color, fg=palette.win95, padx=10, pady=3).pack(side="left")

    tk.Button(badge_row, text="✕  DONE WITH ORDER", font=("Segoe UI", 8, "bold"),
              bg=palette.bg, fg="#95a5a6", activeforeground=palette.danger, relief="flat",
              command=lambda: [window.attributes("-fullscreen", False), start_login(window)]
              ).pack(side="right")

    # Scrollable Tray
    cart_scroll_frame = ctk.CTkScrollableFrame(tray, fg_color=palette.bg, corner_radius=0)
    cart_scroll_frame.pack(fill="both", expand=True)

    def _on_mousewheel(event):
        x, y = event.x_root, event.y_root
        tx, ty, tw, th = tray.winfo_rootx(), tray.winfo_rooty(), tray.winfo_width(), tray.winfo_height()
        if tx <= x <= tx + tw and ty <= y <= ty + th:
            cart_scroll_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            menu_scroll._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    window.bind_all("<MouseWheel>", _on_mousewheel)

    # 4. Footer
    footer = tk.Frame(tray, bg=palette.bg, pady=24, padx=24, bd=1, relief="solid")
    footer.pack(side="bottom", fill="x")
    tot_row = tk.Frame(footer, bg=palette.bg)
    tot_row.pack(fill="x", pady=(0, 16))
    tk.Label(tot_row, text="GRAND TOTAL", font=("Segoe UI", 11, "bold"), bg=palette.bg, fg=palette.text).pack(side="left")
    total_lbl = tk.Label(tot_row, text="₱0.00", font=("Segoe UI", 26, "bold"), fg=palette.primary, bg=palette.bg)
    total_lbl.pack(side="right")

    tk.Entry(footer, textvariable=cash_var, justify="center", font=("Segoe UI", 22), bd=0, bg="#f1f2f6", fg=palette.text).pack(fill="x",
                                                                                                              pady=(0,
                                                                                                                    16),
                                                                                                              ipady=10)
    tk.Button(footer, text="PLACE ORDER", bg=palette.secondary, fg=palette.win95, font=("Segoe UI", 15, "bold"), height=2,
              relief="flat", command=handle_checkout).pack(fill="x")

    update_ui()