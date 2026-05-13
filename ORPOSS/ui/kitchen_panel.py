import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import sys

from db.orders_db import advance_order, get_orders
from utils.helper import peso
from utils.palette import palette
from ui.window_utils import clear_main_window

STATUS_COLORS = {
    "preparing": palette.primary,
    "serving":   palette.secondary,
    "claimed":   palette.text,
}
NEXT_BTN = {
    "preparing": "MARK SERVING",
    "serving":   "MARK CLAIMED",
}

def start_kitchen_panel(window):
    from ui.login import start_login

    clear_main_window(window)
    window.attributes("-fullscreen", True)
    window.bind("<Escape>", lambda e: window.attributes("-fullscreen", False))
    window.bind("<F11>",    lambda e: window.attributes("-fullscreen",
                                not window.attributes("-fullscreen")))

    def on_closing():
        if messagebox.askokcancel("Quit", "Exit the system?"):
            window.destroy(); sys.exit()
    window.protocol("WM_DELETE_WINDOW", on_closing)

    if isinstance(window, ctk.CTk):
        window.configure(fg_color=palette.bg)
    else:
        window.configure(bg=palette.bg)

    # ── Header ────────────────────────────────────────────────────────────────
    header = tk.Frame(window, bg=palette.text, height=70)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="🍳  KITCHEN PANEL",
             font=("Segoe UI", 22, "bold"),
             fg=palette.bg, bg=palette.text).pack(side="left", padx=28)

    tk.Label(header, text="STAFF ORDER MANAGEMENT",
             font=("Segoe UI", 11), fg=palette.bg, bg=palette.text
             ).pack(side="right", padx=28)

    tk.Button(header, text="← BACK TO LOGIN",
              font=("Segoe UI", 9, "bold"),
              bg=palette.danger, fg="white", relief="flat", cursor="hand2",
              padx=12,
              command=lambda: [window.attributes("-fullscreen", False),
                               start_login(window)]
              ).pack(side="right", padx=12, pady=16)

    # ── Body: 3 columns — Preparing | Serving | Claimed ───────────────────────
    body = tk.Frame(window, bg=palette.bg)
    body.pack(fill="both", expand=True, padx=20, pady=20)

    columns = ["preparing", "serving", "claimed"]
    col_titles = {
        "preparing": "🔥  PREPARING",
        "serving":   "🛎  SERVING",
        "claimed":   "✅  CLAIMED",
    }
    NEXT_BTN_COLORS = {
        "preparing": palette.secondary,
        "serving":   palette.primary,
    }

    col_frames  = {}   # scrollable inner frame per status
    count_lbls  = {}

    for i, status in enumerate(columns):
        body.grid_columnconfigure(i, weight=1)

        # column wrapper
        col_wrap = tk.Frame(body, bg="white", bd=1, relief="solid")
        col_wrap.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else 8, 0))
        body.grid_rowconfigure(0, weight=1)

        # column header
        col_hdr = tk.Frame(col_wrap, bg=STATUS_COLORS[status], height=48)
        col_hdr.pack(fill="x")
        col_hdr.pack_propagate(False)
        tk.Label(col_hdr, text=col_titles[status],
                 font=("Segoe UI", 13, "bold"),
                 fg="white", bg=STATUS_COLORS[status]).pack(side="left", padx=16)
        count_lbl = tk.Label(col_hdr, text="0",
                             font=("Segoe UI", 13, "bold"),
                             fg="white", bg=STATUS_COLORS[status])
        count_lbl.pack(side="right", padx=16)
        count_lbls[status] = count_lbl

        # scrollable card area
        canvas = tk.Canvas(col_wrap, bg="white", highlightthickness=0)
        sb = tk.Scrollbar(col_wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="white")
        inner.bind("<Configure>",
                   lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        col_frames[status] = (inner, canvas)

    # ── Card builder ─────────────────────────────────────────────────────────
    def compact_items(summary):
        return "  |  ".join(f"{d['qty']}× {item}" for item, d in summary.items())

    def make_card(parent, order):
        status = order["status"]
        accent = STATUS_COLORS[status]

        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=8)

        # top bar
        top = tk.Frame(card, bg=accent)
        top.pack(fill="x")
        tk.Label(top, text=f"ORDER #{order['invoice_no'][-4:]}",
                 font=("Segoe UI", 18, "bold"),
                 fg="white", bg=accent, padx=12, pady=8).pack(side="left")
        tk.Label(top, text=f"{order['order_type'].upper()}",
                 font=("Segoe UI", 9, "bold"),
                 fg=accent, bg="white", padx=8, pady=4).pack(side="right", padx=10, pady=8)

        # items
        tk.Label(card, text=compact_items(order["summary"]),
                 font=("Segoe UI", 10), fg=palette.teal, bg="white",
                 wraplength=260, justify="left", padx=12, pady=6
                 ).pack(anchor="w")

        # time + total
        info_row = tk.Frame(card, bg="white")
        info_row.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(info_row, text=f"Placed {order['created_at']}",
                 font=("Segoe UI", 8), fg=palette.teal, bg="white").pack(side="left")
        tk.Label(info_row, text=peso(order["total"]),
                 font=("Segoe UI", 10, "bold"), fg=palette.primary, bg="white"
                 ).pack(side="right")

        # action button (not on claimed)
        btn_text = NEXT_BTN.get(status)
        if btn_text:
            btn_color = NEXT_BTN_COLORS.get(status, palette.secondary)
            tk.Button(card, text=btn_text,
                      font=("Segoe UI", 9, "bold"),
                      bg=btn_color, fg="white", relief="flat",
                      cursor="hand2", pady=8,
                      command=lambda inv=order["invoice_no"]: [
                          advance_order(inv), refresh()]
                      ).pack(fill="x", padx=10, pady=(0, 10))

    # ── Refresh loop ─────────────────────────────────────────────────────────
    def refresh():
        for status in columns:
            inner, canvas = col_frames[status]
            for w in inner.winfo_children():
                w.destroy()

            orders = get_orders(status)
            count_lbls[status].config(text=str(len(orders)))

            if not orders:
                empty_msgs = {
                    "preparing": "No orders being prepared",
                    "serving":   "No orders ready to serve",
                    "claimed":   "No claimed orders yet",
                }
                tk.Label(inner, text=empty_msgs[status],
                         font=("Segoe UI", 10, "italic"),
                         fg=palette.teal, bg="white", pady=40
                         ).pack()
            else:
                for order in orders:
                    make_card(inner, order)

            inner.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        if window.winfo_exists():
            window.after(1500, refresh)

    refresh()

    # ── Pusher real-time subscription ─────────────────────────────────────────
    def on_pusher_event(data):
        # Called from background thread — schedule UI refresh on main thread
        if window.winfo_exists():
            window.after(0, refresh)

    from utils.pusher_client import subscribe
    subscribe("orders", "new-order",    on_pusher_event)
    subscribe("orders", "order-updated", on_pusher_event)
