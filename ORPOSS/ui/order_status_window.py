import tkinter as tk

from db.orders_db import advance_order, get_orders
from utils.sound import play
from utils.helper import peso
from utils.palette import palette

STATUS_COLORS = {
    "preparing": palette.primary,
    "serving":   palette.secondary,
    "claimed":   palette.text,
}
STATUS_LABELS = {
    "preparing": "PREPARING",
    "serving":   "SERVING",
    "claimed":   "CLAIMED",
}
NEXT_BUTTONS = {
    "preparing": "MARK SERVING",
    "serving":   "MARK CLAIMED",
}

# Poll interval — Pusher handles instant updates; this is just a safety net
_POLL_MS = 10_000   # 10 seconds (was 1500ms — reduces DB hits & Pusher credit usage)


def open_order_status_window(parent_window, allow_status_update=False):
    attr_name = "_staff_order_window" if allow_status_update else "_order_status_window"
    existing  = getattr(parent_window, attr_name, None)
    if existing and existing.winfo_exists():
        existing.lift()
        existing.focus_force()
        return existing

    win = tk.Toplevel(parent_window)
    win._keep_on_screen_change = True
    setattr(parent_window, attr_name, win)
    win.title("Staff Order Window" if allow_status_update else "Customer Order Window")
    win.geometry("1120x620")
    win.configure(bg=palette.bg)
    win.minsize(960, 520)

    def cleanup():
        setattr(parent_window, attr_name, None)
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", cleanup)

    # ── Header ────────────────────────────────────────────────────────────────
    header = tk.Frame(win, bg=palette.text, height=82)
    header.pack(fill="x")
    header.pack_propagate(False)
    title    = "STAFF ORDER WINDOW"     if allow_status_update else "CUSTOMER ORDER WINDOW"
    subtitle = "MANAGE CUSTOMER ORDERS" if allow_status_update else "PREPARING / SERVING"
    tk.Label(header, text=title,    font=("Segoe UI", 24, "bold"), fg=palette.bg, bg=palette.text).pack(side="left",  padx=28)
    tk.Label(header, text=subtitle, font=("Segoe UI", 12, "bold"), fg=palette.bg, bg=palette.text).pack(side="right", padx=28)

    body = tk.Frame(win, bg=palette.bg)
    body.pack(fill="both", expand=True, padx=18, pady=18)

    visible_statuses = ("preparing", "serving", "claimed") if allow_status_update else ("preparing", "serving")
    for col in range(len(visible_statuses)):
        body.grid_columnconfigure(col, weight=1)
    body.grid_rowconfigure(1, weight=1)

    count_labels = {}
    list_frames  = {}

    for col, status in enumerate(visible_statuses):
        count_labels[status] = tk.Label(
            body, bg=palette.bg, fg=STATUS_COLORS[status], font=("Segoe UI", 13, "bold")
        )
        count_labels[status].grid(row=0, column=col, sticky="w", padx=10, pady=(0, 8))
        list_frames[status] = tk.Frame(body, bg=palette.bg)
        if len(visible_statuses) == 2:
            padx = (0, 9) if col == 0 else (9, 0)
        else:
            padx = (0, 9) if col == 0 else (9, 9) if col == 1 else (9, 0)
        list_frames[status].grid(row=1, column=col, sticky="nsew", padx=padx)

    def compact_items(summary):
        return ", ".join(f"{data['qty']}x {item}" for item, data in summary.items())

    def make_empty(parent, text):
        box = tk.Frame(parent, bg=palette.text, bd=1, relief="solid")
        box.pack(fill="x", padx=10, pady=10)
        tk.Label(box, text=text, font=("Segoe UI", 12, "italic"),
                 fg=palette.teal, bg=palette.text, pady=38).pack(fill="x")

    def make_card(parent, order, accent):
        if not allow_status_update:
            text_color = "white" if order["status"] == "serving" else palette.text
            
            card = tk.Frame(parent, bg=accent, bd=0, relief="flat")
            card.pack(fill="x", padx=10, pady=10)
            
            tk.Label(card, text=f"ORDER #{order['invoice_no'][-4:]}",
                    font=("Segoe UI", 34, "bold"), 
                    fg=text_color,
                    bg=accent, pady=22).pack(fill="x")
                    
            tk.Label(card, text=STATUS_LABELS[order["status"]],
                    font=("Segoe UI", 12, "bold"), 
                    fg=text_color,
                    bg=accent, pady=6).pack(fill="x")
            return

        card = tk.Frame(parent, bg=palette.text, bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=8)

        top = tk.Frame(card, bg="white")
        top.pack(fill="x", padx=14, pady=(12, 2))
        tk.Label(top, text=f"ORDER #{order['invoice_no'][-4:]}",
                 font=("Segoe UI", 18, "bold"), fg=accent, bg="white").pack(side="left")
        tk.Label(top, text=order["status"].upper(),
                 font=("Segoe UI", 9, "bold"), fg="white", bg=accent,
                 padx=8, pady=3).pack(side="right")

        details = f"{order['order_type']} | {order['payment_mode'].upper()} | {peso(order['total'])}"
        tk.Label(card, text=details, font=("Segoe UI", 10, "bold"),
                 fg=palette.text, bg="white").pack(anchor="w", padx=14)
        tk.Label(card, text=compact_items(order["summary"])[:82],
                 font=("Segoe UI", 9), fg=palette.teal, bg="white",
                 wraplength=340, justify="left").pack(anchor="w", padx=14, pady=(2, 10))

        time_text = f"Placed {order['created_at']}"
        if order.get("claimed_at"):
            time_text = f"Claimed {order['claimed_at']}"
        elif order.get("serving_at"):
            time_text = f"Serving {order['serving_at']}"

        bottom = tk.Frame(card, bg="white")
        bottom.pack(fill="x", padx=14, pady=(0, 12))
        tk.Label(bottom, text=time_text, font=("Segoe UI", 8),
                 fg=palette.teal, bg="white").pack(side="left")

        if allow_status_update and order["status"] in NEXT_BUTTONS:
            tk.Button(bottom, text=NEXT_BUTTONS[order["status"]],
                      font=("Segoe UI", 8, "bold"), bg=palette.secondary, fg="white",
                      relief="flat", cursor="hand2",
                      command=lambda inv=order["invoice_no"]: [advance_order(inv), refresh()]
                      ).pack(side="right")

    _poll_id = [None]

    def refresh():
        if not win.winfo_exists():
            return
        for frame in list_frames.values():
            for child in frame.winfo_children():
                child.destroy()

        empty_text = {
            "preparing": "No orders being prepared",
            "serving":   "No orders ready to serve",
            "claimed":   "No claimed orders yet",
        }
        for status in visible_statuses:
            status_orders = get_orders(status)
            count_labels[status].config(text=f"{STATUS_LABELS[status]} ({len(status_orders)})")
            if status_orders:
                for order in status_orders:
                    make_card(list_frames[status], order, STATUS_COLORS[status])
            else:
                make_empty(list_frames[status], empty_text[status])

        if _poll_id[0]:
            win.after_cancel(_poll_id[0])
        _poll_id[0] = win.after(_POLL_MS, refresh)

    refresh()

    # ── Pusher: triggers immediate refresh on order events ────────────────────
    def on_pusher_event(data):
        if win.winfo_exists():
            if data.get("status") == "serving":
                play("PopClose.wav")
            elif data.get("status") == "preparing":
                play("PopOpen.wav")
            win.after(0, refresh)

    from utils.pusher_client import subscribe
    subscribe("orders", "new-order",     on_pusher_event)
    subscribe("orders", "order-updated", on_pusher_event)

    return win
