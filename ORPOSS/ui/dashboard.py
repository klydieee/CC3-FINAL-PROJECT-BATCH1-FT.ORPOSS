"""
dashboard.py  –  Main POS screen (ORPOSS logic + CTk/Win-95 aesthetic from POS_SYSTEM)
"""
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import datetime
import sys
import os

from data.inventory import inventory
from data.order_queue import add_order
from utils.helper import peso
from utils.receipt_generator import generate_receipt_file
from ui.receipt_popup import show_receipt_popup
from ui.order_review import show_order_review
from ui.admin_panel import start_admin_panel
from ui.login import start_login
from ui.window_utils import clear_main_window
from ui.order_status_window import open_order_status_window

# ── palette ───────────────────────────────────────────────────────────────────
BG_COLOR       = "#f8f9fa"
TEXT_COLOR     = "#2c3e50"
PRIMARY_COLOR  = "#e67e22"   # orange totals
SECONDARY_COLOR= "#2ecc71"   # green confirm
WIN95_GREY     = "#d0d0d0"
TEAL           = "#1a3c40"


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
    cart         = {}      # {name: qty}
    buttons      = {}      # {name: CTkButton}
    stock_labels = {}      # {name: CTkLabel}  so update_ui can refresh QTY text
    cash_var = tk.StringVar(value="₱")

    def format_cash(*_):
        val    = cash_var.get()
        digits = "".join(filter(str.isdigit, val))
        cash_var.set(f"₱{digits}" if digits else "₱")
    cash_var.trace_add("write", format_cash)

    def get_total():
        return sum(inventory[n]["price"] * q for n, q in cart.items())

    # ── helpers ───────────────────────────────────────────────────────────────
    def save_inventory():
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "..", "data", "inventory.py")
        with open(path, "w") as f:
            f.write(f"inventory = {repr(inventory)}")

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

    # ── binding helpers ───────────────────────────────────────────────────────
    def walk(widget):
        """Yield widget and all descendants recursively."""
        yield widget
        for child in widget.winfo_children():
            yield from walk(child)

    # ── UI refresh ────────────────────────────────────────────────────────────
    def update_ui():
        # rebuild tray list
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
                     bg="white", fg=TEXT_COLOR).pack(side="top", anchor="w")
            tk.Label(info, text=f"{qty}x – {peso(inventory[name]['price']*qty)}",
                     font=("Segoe UI", 9), fg=PRIMARY_COLOR, bg="white"
                     ).pack(side="top", anchor="w")

            ctrl = tk.Frame(row, bg="white")
            ctrl.pack(side="right")
            tk.Button(ctrl, text="−", width=2, bg="#e74c3c", fg="white",
                      relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, -1)).pack(side="left", padx=2)
            tk.Label(ctrl, text=str(qty),
                     font=("Segoe UI", 10, "bold"), bg="white", width=3
                     ).pack(side="left")
            tk.Button(ctrl, text="+", width=2, bg=SECONDARY_COLOR, fg="white",
                      relief="flat", font=("Arial", 10, "bold"),
                      command=lambda n=name: adjust_qty(n, 1)).pack(side="left", padx=2)

        cart_scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # update total label
        total_lbl.config(text=peso(get_total()))

        # update card visuals only — bindings are set once in make_box and never changed
        for name, frame in buttons.items():
            s = inventory[name]["stock"]
            target_color = "#e0e0e0" if s <= 0 else WIN95_GREY
            if frame.cget("fg_color") != target_color:
                frame.configure(fg_color=target_color)
            lbl = stock_labels.get(name)
            if lbl:
                lbl.configure(text=f"QTY: {s}",
                              text_color="red" if s < 5 else "green")

    # ── checkout ──────────────────────────────────────────────────────────────
    def handle_checkout():
        total = get_total()
        if not cart:
            messagebox.showwarning("Empty Tray", "Please add items to your tray before placing an order.")
            return

        try:
            raw   = cash_var.get().replace("₱", "").strip()
            cash  = float(raw) if raw else 0.0
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
            add_order(inv_no, order_type, mode, total, summary)
            cart.clear()
            cash_var.set("₱")
            save_inventory()
            def go_home():
                window.attributes("-fullscreen", False)
                start_login(window)
            show_receipt_popup(window, cash, change, inv_no, total, summary, mode, on_done=go_home)

        show_order_review(window, cash, total, summary, finalize)

    # ── LAYOUT ────────────────────────────────────────────────────────────────

    # 1. Sidebar
    sidebar = tk.Frame(window, bg=TEXT_COLOR, width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="ORPOSS",
             fg="white", bg=TEXT_COLOR,
             font=("Segoe UI", 18, "bold")).pack(pady=(30, 4))
    tk.Label(sidebar, text="POS Terminal",
             fg="#95a5a6", bg=TEXT_COLOR,
             font=("Segoe UI", 9)).pack(pady=(0, 30))

    if user_role == "Admin":
        tk.Button(sidebar, text="📺  CUSTOMER\n    SCREEN",
                  bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
                  relief="flat", cursor="hand2", pady=10,
                  command=lambda: open_order_status_window(window, allow_status_update=False)
                  ).pack(fill="x", padx=15, pady=(0, 8))

        tk.Button(sidebar, text="🍳  KITCHEN\n    PANEL",
                  bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
                  relief="flat", cursor="hand2", pady=10,
                  command=lambda: open_order_status_window(window, allow_status_update=True)
                  ).pack(fill="x", padx=15)

    if user_role == "Admin":
        tk.Button(
            sidebar, text="ADMIN PANEL",
            bg="#34495e", fg="white", font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2",
            command=lambda: start_admin_panel(
                window, lambda: start_dashboard(window, user_role))
        ).pack(side="bottom", fill="x", pady=20, padx=15)

    # 2. Menu grid (CTk scrollable frame + dynamic column spanning)
    menu_scroll = ctk.CTkScrollableFrame(window, fg_color=BG_COLOR,
                                         corner_radius=0)
    menu_scroll.pack(side="left", fill="both", expand=True)

    tk.Label(menu_scroll, text="SELECT YOUR MEAL",
             font=("Segoe UI", 24, "bold"),
             bg=BG_COLOR, fg=TEXT_COLOR).pack(
                 anchor="w", padx=60, pady=(40, 20))

    # inner frame is what we grid cards into
    items_area = tk.Frame(menu_scroll, bg=BG_COLOR)
    items_area.pack(fill="both", expand=True)

    # pre-build one frame per item (don't recreate on every resize)
    item_frames = {}

    def make_box(n):
        frame = ctk.CTkFrame(items_area, width=200, height=200,
                             corner_radius=0,
                             border_width=2, border_color="#808080",
                             fg_color=WIN95_GREY)
        frame.grid_propagate(False)

        try:
            from PIL import Image
            img_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "assets", "items", f"{n.lower()}.png")
            img_data = ctk.CTkImage(Image.open(img_path), size=(90, 90))
            ctk.CTkLabel(frame, image=img_data, text="", cursor="hand2").pack(pady=(8, 0))
        except Exception:
            ctk.CTkLabel(frame, text="[ NO IMAGE ]",
                         font=("Courier", 10), cursor="hand2").pack(pady=(8, 0))

        ctk.CTkLabel(frame, text=n.upper(),
                     font=("Courier", 13, "bold"),
                     text_color="black", cursor="hand2").pack()

        s = inventory[n]["stock"]
        lbl_stock = ctk.CTkLabel(frame, text=f"QTY: {s}",
                                 font=("Courier", 11),
                                 text_color="red" if s < 5 else "green",
                                 cursor="hand2")
        lbl_stock.pack()
        stock_labels[n] = lbl_stock

        ctk.CTkLabel(frame, text=peso(inventory[n]["price"]),
                     font=("Courier", 13),
                     text_color=TEAL, cursor="hand2").pack(pady=(0, 6))

        # whole card is the button — bindings set once, stock checked at click time
        def on_click(e, nm=n):
            if inventory[nm]["stock"] > 0:
                adjust_qty(nm, 1)

        def on_enter(e, f=frame, nm=n):
            if inventory[nm]["stock"] > 0:
                f.configure(fg_color="#bdbdbd")
        def on_leave(e, f=frame, nm=n):
            if inventory[nm]["stock"] > 0:
                f.configure(fg_color=WIN95_GREY)

        frame.configure(cursor="hand2")
        for widget in walk(frame):
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            try: widget.configure(cursor="hand2")
            except Exception: pass

        # store frame as the "button" so update_ui can disable it
        buttons[n] = frame
        return frame

    for name in inventory:
        item_frames[name] = make_box(name)

    _grid_job = [None]

    def recalculate_grid():
        for slave in items_area.grid_slaves():
            slave.grid_forget()
        w = items_area.winfo_width()
        num_cols = max(1, w // 224)
        r, c = 0, 0
        for name in inventory:
            item_frames[name].grid(row=r, column=c, padx=12, pady=12, sticky="nsew")
            c += 1
            if c >= num_cols:
                c = 0
                r += 1
        for i in range(num_cols):
            items_area.grid_columnconfigure(i, weight=1)

    def schedule_grid(e=None):
        if _grid_job[0]:
            items_area.after_cancel(_grid_job[0])
        _grid_job[0] = items_area.after(50, recalculate_grid)

    items_area.bind("<Configure>", schedule_grid)

    # 3. Tray panel
    tray = tk.Frame(window, bg="white", width=420)
    tray.pack(side="right", fill="y")
    tray.pack_propagate(False)

    hdr = tk.Frame(tray, bg="white", pady=16)
    hdr.pack(fill="x")

    title_row = tk.Frame(hdr, bg="white")
    title_row.pack(fill="x", padx=24)
    tk.Label(title_row, text="YOUR TRAY",
             font=("Segoe UI", 16, "bold"), bg="white").pack(side="left")
    tk.Button(title_row, text="EMPTY", bg="#e74c3c", fg="white",
              font=("Segoe UI", 8, "bold"), relief="flat", padx=12,
              command=empty_cart).pack(side="right")

    # order type badge + done button
    badge_row = tk.Frame(hdr, bg="white")
    badge_row.pack(fill="x", padx=24, pady=(6, 0))
    badge_color = "#2c3e50" if order_type == "Dine-In" else "#e67e22"
    badge_emoji = "🍽️" if order_type == "Dine-In" else "🥡"
    tk.Label(badge_row, text=f"{badge_emoji} {order_type.upper()}",
             font=("Segoe UI", 9, "bold"),
             bg=badge_color, fg="white",
             padx=10, pady=3).pack(side="left")
    tk.Button(badge_row, text="✕  DONE WITH ORDER",
              font=("Segoe UI", 8, "bold"),
              bg="white", fg="#95a5a6",
              activeforeground="#e74c3c",
              relief="flat", cursor="hand2",
              command=lambda: [window.attributes("-fullscreen", False), start_login(window)]
              ).pack(side="right")

    canvas_f = tk.Frame(tray, bg="white")
    canvas_f.pack(fill="both", expand=True)
    canvas    = tk.Canvas(canvas_f, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_f, orient="vertical", command=canvas.yview)
    cart_scroll_frame = tk.Frame(canvas, bg="white")
    cwin = canvas.create_window((0, 0), window=cart_scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(cwin, width=e.width))

    def _on_mousewheel(event):
        x, y = event.x_root, event.y_root

        tx = tray.winfo_rootx()
        ty = tray.winfo_rooty()
        tw = tray.winfo_width()
        th = tray.winfo_height()

        if tx <= x <= tx + tw and ty <= y <= ty + th:
            bbox = canvas.bbox("all")
            if bbox and bbox[3] > canvas.winfo_height():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            mc = menu_scroll._parent_canvas
            bbox = mc.bbox("all")
            if bbox and bbox[3] > mc.winfo_height():
                mc.yview_scroll(int(-1 * (event.delta / 120)), "units")

    window.bind_all("<MouseWheel>", _on_mousewheel)

    # checkout footer
    footer = tk.Frame(tray, bg="#fdfdfd", pady=24, padx=24,
                      bd=1, relief="solid")
    footer.pack(side="bottom", fill="x")

    tot_row = tk.Frame(footer, bg="#fdfdfd")
    tot_row.pack(fill="x", pady=(0, 16))
    tk.Label(tot_row, text="GRAND TOTAL",
             font=("Segoe UI", 11, "bold"), bg="#fdfdfd", fg="#7f8c8d"
             ).pack(side="left")
    total_lbl = tk.Label(tot_row, text="₱0.00",
                         font=("Segoe UI", 26, "bold"),
                         fg=PRIMARY_COLOR, bg="#fdfdfd")
    total_lbl.pack(side="right")

    tk.Entry(footer, textvariable=cash_var, justify="center",
             font=("Segoe UI", 22), bd=0, bg="#f1f2f6"
             ).pack(fill="x", pady=(0, 16), ipady=10)

    tk.Button(footer, text="PLACE ORDER",
              bg=SECONDARY_COLOR, fg="white",
              font=("Segoe UI", 15, "bold"),
              height=2, relief="flat",
              command=handle_checkout).pack(fill="x")

    # quick cash shortcuts
    qs = tk.Frame(footer, bg="#fdfdfd")
    qs.pack(fill="x", pady=(16, 0))
    for amt in [100, 200, 500, 1000]:
        tk.Button(qs, text=f"₱{amt}",
                  font=("Segoe UI", 10, "bold"), bg="white", relief="flat",
                  highlightthickness=1, highlightbackground="#dcdde1",
                  command=lambda a=amt: cash_var.set(f"₱{a}")
                  ).pack(side="left", padx=3, expand=True, fill="x")

    update_ui()