"""
db/orders_db.py
Persists orders + status changes to MySQL.
Fires Pusher events so other terminals update in real time.
Falls back to in-memory only when offline.
"""
import datetime
from db.connection import execute, is_online
from utils.pusher_client import push_event

orders     = []
STATUS_FLOW = ("preparing", "serving", "claimed")


def add_order(invoice_no, order_type, payment_mode, total, summary, cash=0, change_amt=0):
    now   = datetime.datetime.now()
    order = {
        "invoice_no":   invoice_no,
        "order_type":   order_type,
        "payment_mode": payment_mode,
        "total":        total,
        "cash":         cash,
        "change_amt":   change_amt,
        "status":       "preparing",
        "summary":      summary,
        "created_at":   now.strftime("%I:%M %p"),
        "serving_at":   "",
        "claimed_at":   "",
    }
    if is_online():
        execute(
            """INSERT INTO orders
               (invoice_no, order_type, payment_mode, total, cash, change_amt, status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,'preparing',%s)""",
            (invoice_no, order_type, payment_mode, total, cash, change_amt, now)
        )
        for name, data in summary.items():
            execute(
                "INSERT INTO order_lines (invoice_no, name, qty, price, product_id) VALUES (%s,%s,%s,%s,%s)",
                (invoice_no, name, data["qty"], data["price"], data.get("product_id"))
            )
    else:
        orders.append(order)

    push_event("orders", "new-order", {
        "invoice_no":   invoice_no,
        "order_type":   order_type,
        "payment_mode": payment_mode,
        "total":        str(total),
        "status":       "preparing",
    })
    return order


def advance_order(invoice_no):
    if is_online():
        row = execute("SELECT status FROM orders WHERE invoice_no=%s",
                      (invoice_no,), fetch="one")
        if not row:
            return None
        current = row["status"]
        if current not in STATUS_FLOW:
            return None
        idx = STATUS_FLOW.index(current)
        if idx >= len(STATUS_FLOW) - 1:
            return None
        new_status = STATUS_FLOW[idx + 1]
        now = datetime.datetime.now()
        execute(f"UPDATE orders SET status=%s, {new_status}_at=%s WHERE invoice_no=%s",
                (new_status, now, invoice_no))
        push_event("orders", "order-updated", {"invoice_no": invoice_no, "status": new_status})
        return {"invoice_no": invoice_no, "status": new_status}
    else:
        for order in orders:
            if order["invoice_no"] == invoice_no:
                idx = STATUS_FLOW.index(order["status"])
                if idx >= len(STATUS_FLOW) - 1:
                    return order
                return _set_status_offline(order, STATUS_FLOW[idx + 1])
    return None


def cancel_order(invoice_no):
    """Cancel a preparing order. Returns True on success."""
    if is_online():
        row = execute("SELECT status FROM orders WHERE invoice_no=%s",
                      (invoice_no,), fetch="one")
        if not row:
            return False
        if row["status"] != "preparing":
            return False  # can only cancel while still preparing
        execute("UPDATE orders SET status='cancelled' WHERE invoice_no=%s",
                (invoice_no,))
        push_event("orders", "order-updated", {"invoice_no": invoice_no, "status": "cancelled"})
        return True
    else:
        for order in orders:
            if order["invoice_no"] == invoice_no and order["status"] == "preparing":
                order["status"] = "cancelled"
                push_event("orders", "order-updated",
                           {"invoice_no": invoice_no, "status": "cancelled"})
                return True
    return False


def _set_status_offline(order, status):
    order["status"] = status
    now = datetime.datetime.now()
    order[f"{status}_at"] = now.strftime("%I:%M %p")
    push_event("orders", "order-updated",
               {"invoice_no": order["invoice_no"], "status": status})
    return order


def get_orders(status=None):
    if is_online():
        return _fetch_from_db(status)
    if status is None:
        return [o for o in orders if o["status"] != "cancelled"]
    return [o for o in orders if o["status"] == status]


def _fetch_from_db(status=None):
    if status:
        where  = "WHERE o.status = %s"
        params = (status,)
    else:
        # Exclude cancelled and claimed from the live view by default
        where  = "WHERE o.status IN ('preparing','serving')"
        params = ()

    rows = execute(
        f"""SELECT o.invoice_no, o.order_type, o.payment_mode, o.total,
                   o.status, o.created_at, o.serving_at, o.claimed_at,
                   ol.name AS item_name, ol.qty, ol.price AS item_price
            FROM orders o
            JOIN order_lines ol ON o.invoice_no = ol.invoice_no
            {where}
            ORDER BY o.created_at ASC""",
        params, fetch="all"
    )
    if not rows:
        return []

    grouped = {}
    for row in rows:
        inv = row["invoice_no"]
        if inv not in grouped:
            grouped[inv] = {
                "invoice_no":   inv,
                "order_type":   row["order_type"],
                "payment_mode": row["payment_mode"],
                "total":        float(row["total"]),
                "status":       row["status"],
                "summary":      {},
                "created_at":   row["created_at"].strftime("%I:%M %p") if hasattr(row["created_at"], "strftime") else str(row["created_at"]),
                "serving_at":   row["serving_at"].strftime("%I:%M %p") if row.get("serving_at") else "",
                "claimed_at":   row["claimed_at"].strftime("%I:%M %p") if row.get("claimed_at") else "",
            }
        grouped[inv]["summary"][row["item_name"]] = {
            "qty":   row["qty"],
            "price": float(row["item_price"]),
        }
    return list(grouped.values())
