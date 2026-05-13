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
from ui.admin_panel import start_admin_panel
from ui.login import start_login
from ui.window_utils import clear_main_window
from ui.order_status_window import open_order_status_window
from utils.palette import palette


def start_dashboard(window, user_role="Client", order_type="Dine-In"):
    """Clears *window* and renders the full POS dashboard."""
    clear_main_window(window)

    window.attributes("-fullscreen", True)
    window.bind("<Escape>",
                lambda e: window.attributes("-fullscreen", False))
    window.bind("<F11>",
                lambda e: window.attributes(
                    "-fullscreen", not window.attributes("-fullscreen")))

    def on_closing():
        if messagebox.askokcancel("Quit", "Exit the system?"):
            window.destroy()
            sys.exit()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    # ── state ─────────────────────────────────────────────────────────────────
    cart = {}  # {name: qty}
    buttons = {}  # {name: CTkButton}
    stock_labels = {}  # {name: CTkLabel}
    cash_var = tk.StringVar(value="₱")

    def format_cash(*_):
        val = cash_var.get()
        digits = "".join(filter(str.isdigit, val))
        cash_var.set(f"₱{digits}" if digits else "₱")

    cash_var.trace_add("write", format_cash)

    def get_total():
        return sum(inventory[n]["price"] * q for n, q in cart.items())

    # ── helpers ───────────────────────────────────────────────────────────────
    def save_inventory():
        from db.products_db import save_stock
        for name in cart:
            save_stock(name)

    def empty_cart():
        if not cart:
            return
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
            if cart[name] <= 0:
                del cart[name]
        update_ui()

    def walk(widget):
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    # ── UI refresh ────────────────────────────────────────────────────────────
    def update_ui():
        for w in cart_scroll_frame.winfo_children():
            w.destroy()

        if not cart:
            tk.Label(cart_scroll_frame,
                     text="Your tray is empty",
                     font=("Segoe UI", 11, "italic"),
                     fg="#95a5a6", bg="white", pady=60).pack()

        for name, qty in cart.items():
            row = tk.Frame(cart_scroll_frame, bg="white", pady=12)
            row.pack(fill="x", padx=15, pady=2)

            info = tk.Frame(row, bg="white")
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=name.upper(),
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg=palette.text).pack(side="top", anchor="w")
            tk.Label(info, text=f"{qty}x – {peso(inventory[name]['price'] * qty)}",
                     font=("Segoe UI", 9), fg=palette.primary, bg="white"
                     ).pack(side="top", anchor="w")

            ctrl = tk.Frame(row, bg="white")
            ctrl.pack(side="right")
            tk.Button(ctrl, text="−", width=2, bg=palette.danger, fg="white",
                      relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, -1)).pack(side="left", padx=2)
            tk.Label(ctrl, text=str(qty),
                     font=("Segoe UI", 10, "bold"), bg="white", width=3
                     ).pack(side="left")
            tk.Button(ctrl, text="+", width=2, bg=palette.secondary, fg="white",
                      relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, 1)).pack(side="left", padx=2)

        cart_scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        total_lbl.config(text=peso(get_total()))

        for name, frame in buttons.items():
            s = inventory[name]["stock"]
            target_color = "#e0e0e0" if s <= 0 else palette.win95
            if frame.cget("fg_color") != target_color:
                frame.configure(fg_color=target_color)
            lbl = stock_labels.get(name)
            if lbl:
                lbl.configure(text=f"QTY: {s}",
                              text_color=palette.danger if s < 5 else palette.secondary)

    # ── checkout ──────────────────────────────────────────────────────────────
    def handle_checkout():
        total = get_total()
        if not cart:
            messagebox.showwarning("Empty Tray", "Please add items to your tray before placing an order.")
            return

        try:
            raw = cash_var.get().replace("₱", "").strip()
            cash = float(raw) if raw else 0.0
        except ValueError:
            messagebox.showerror("Error", "Invalid cash amount.")
            return

        if cash < total:
            messagebox.showerror("Insufficient",
                                 f"Cash is less than total {peso(total)}")
            return

        summary = {n: {"qty": q, "price": inventory[n]["price"]}
                   for n, q in cart.items()}

        def finalize(mode):
            inv_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            change = cash - total
            generate_receipt_file(cash, change, inv_no, total, summary, mode)
            add_order(inv_no, order_type, mode, total, summary, cash=cash, change_amt=change)
            cart.clear()
            cash_var.set("₱")
            save_inventory()

            def go_home():
                window.attributes("-fullscreen", False)
                start_login(window)

            show_receipt_popup(window, cash, change, inv_no, total, summary, mode, on_done=go_home)

        show_order_review(window, cash, total, summary, finalize)

    # 1. Sidebar
    sidebar = tk.Frame(window, bg=palette.text, width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="ORPOSS",
             fg="white", bg=palette.text,
             font=("Segoe UI", 18, "bold")).pack(pady=(30, 4))
    tk.Label(sidebar, text="POS Terminal",
             fg="#95a5a6", bg=palette.text,
             font=("Segoe UI", 9)).pack(pady=(0, 30))

    if user_role == "Admin":
        for btn_text, kitchen_mode in [("📺  CUSTOMER\n    SCREEN", False), ("🍳  KITCHEN\n    PANEL", True)]:
            tk.Button(sidebar, text=btn_text,
                      bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
                      relief="flat", cursor="hand2", pady=10,
                      command=lambda m=kitchen_mode: open_order_status_window(window, allow_status_update=m)
                      ).pack(fill="x", padx=15, pady=(0, 8))

        tk.Button(
            sidebar, text="ADMIN PANEL",
            bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2",
            command=lambda: start_admin_panel(
                window, lambda: start_dashboard(window, user_role, order_type))
        ).pack(side="bottom", fill="x", pady=20, padx=15)

    # 2. Menu grid
    menu_scroll = ctk.CTkScrollableFrame(window, fg_color=palette.bg, corner_radius=0)
    menu_scroll.pack(side="left", fill="both", expand=True)

    tk.Label(menu_scroll, text="SELECT YOUR MEAL",
             font=("Segoe UI", 24, "bold"),
             bg=palette.bg, fg=palette.text).pack(anchor="w", padx=60, pady=(40, 20))

    items_area = tk.Frame(menu_scroll, bg=palette.bg)
    items_area.pack(fill="both", expand=True)

    item_frames = {}

    def make_box(n):
        frame = ctk.CTkFrame(items_area, width=200, height=200,
                             corner_radius=0,
                             border_width=2, border_color="#808080",
                             fg_color=palette.win95)
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
            ctk.CTkLabel(frame, image=img_data, text="", cursor="hand2").pack(pady=(8, 0))
        except:
            ctk.CTkLabel(frame, text="[ NO IMAGE ]", font=("Courier", 10), cursor="hand2").pack(pady=(8, 0))

        ctk.CTkLabel(frame, text=n.upper(), font=("Courier", 13, "bold"), text_color="black", cursor="hand2").pack()

        s = inventory[n]["stock"]
        lbl_stock = ctk.CTkLabel(frame, text=f"QTY: {s}", font=("Courier", 11),
                                 text_color=palette.danger if s < 5 else palette.secondary,
                                 cursor="hand2")
        lbl_stock.pack()
        stock_labels[n] = lbl_stock

        ctk.CTkLabel(frame, text=peso(inventory[n]["price"]), font=("Courier", 13),
                     text_color=palette.teal, cursor="hand2").pack(pady=(0, 6))

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

    for name in inventory:
        item_frames[name] = make_box(name)

    def recalculate_grid():
        for slave in items_area.grid_slaves(): slave.grid_forget()
        w = items_area.winfo_width()
        num_cols = max(1, w // 224)
        r, c = 0, 0
        for name in inventory:
            item_frames[name].grid(row=r, column=c, padx=12, pady=12, sticky="nsew")
            c += 1
            if c >= num_cols: c, r = 0, r + 1
        for i in range(num_cols): items_area.grid_columnconfigure(i, weight=1)

    items_area.bind("<Configure>", lambda e: items_area.after(50, recalculate_grid))

    # 3. Tray panel
    tray = tk.Frame(window, bg="white", width=420)
    tray.pack(side="right", fill="y")
    tray.pack_propagate(False)

    hdr = tk.Frame(tray, bg="white", pady=16)
    hdr.pack(fill="x")

    title_row = tk.Frame(hdr, bg="white")
    title_row.pack(fill="x", padx=24)
    tk.Label(title_row, text="YOUR TRAY", font=("Segoe UI", 16, "bold"), bg="white").pack(side="left")
    tk.Button(title_row, text="EMPTY", bg=palette.danger, fg="white",
              font=("Segoe UI", 8, "bold"), relief="flat", padx=12,
              command=empty_cart).pack(side="right")

    badge_row = tk.Frame(hdr, bg="white")
    badge_row.pack(fill="x", padx=24, pady=(6, 0))
    badge_color = palette.text if order_type == "Dine-In" else palette.primary
    tk.Label(badge_row, text=f"{'🍽️' if order_type == 'Dine-In' else '🥡'} {order_type.upper()}",
             font=("Segoe UI", 9, "bold"), bg=badge_color, fg="white", padx=10, pady=3).pack(side="left")

    tk.Button(badge_row, text="✕  DONE WITH ORDER", font=("Segoe UI", 8, "bold"),
              bg="white", fg="#95a5a6", activeforeground=palette.danger, relief="flat", cursor="hand2",
              command=lambda: [window.attributes("-fullscreen", False), start_login(window)]
              ).pack(side="right")

    canvas_f = tk.Frame(tray, bg="white")
    canvas_f.pack(fill="both", expand=True)
    canvas = tk.Canvas(canvas_f, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_f, orient="vertical", command=canvas.yview)
    cart_scroll_frame = tk.Frame(canvas, bg="white")
    cwin = canvas.create_window((0, 0), window=cart_scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set, scrollregion=canvas.bbox("all"))
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(cwin, width=e.width))

    def _on_mousewheel(event):
        x, y = event.x_root, event.y_root
        tx, ty, tw, th = tray.winfo_rootx(), tray.winfo_rooty(), tray.winfo_width(), tray.winfo_height()
        if tx <= x <= tx + tw and ty <= y <= ty + th:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            menu_scroll._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    window.bind_all("<MouseWheel>", _on_mousewheel)

    footer = tk.Frame(tray, bg="#fdfdfd", pady=24, padx=24, bd=1, relief="solid")
    footer.pack(side="bottom", fill="x")

    tot_row = tk.Frame(footer, bg="#fdfdfd")
    tot_row.pack(fill="x", pady=(0, 16))
    tk.Label(tot_row, text="GRAND TOTAL", font=("Segoe UI", 11, "bold"), bg="#fdfdfd", fg="#7f8c8d").pack(side="left")
    total_lbl = tk.Label(tot_row, text="₱0.00", font=("Segoe UI", 26, "bold"), fg=palette.primary, bg="#fdfdfd")
    total_lbl.pack(side="right")

    tk.Entry(footer, textvariable=cash_var, justify="center", font=("Segoe UI", 22), bd=0, bg="#f1f2f6").pack(fill="x",
                                                                                                              pady=(0,
                                                                                                                    16),
                                                                                                              ipady=10)

    tk.Button(footer, text="PLACE ORDER", bg=palette.secondary, fg="white", font=("Segoe UI", 15, "bold"),
              height=2, relief="flat", command=handle_checkout).pack(fill="x")

    qs = tk.Frame(footer, bg="#fdfdfd")
    qs.pack(fill="x", pady=(16, 0))
    for amt in [100, 200, 500, 1000]:
        tk.Button(qs, text=f"₱{amt}", font=("Segoe UI", 10, "bold"), bg="white", relief="flat",
                  highlightthickness=1, highlightbackground="#dcdde1",
                  command=lambda a=amt: cash_var.set(f"₱{a}")).pack(side="left", padx=3, expand=True, fill="x")

    update_ui()