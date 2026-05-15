"""
db/orders_db.py
Persists orders + status changes to MySQL.
Also fires Pusher events so other windows update in real time.
Falls back to in-memory only when offline.
"""
import datetime
from db.connection import execute, is_online
from utils.pusher_client import push_event

orders = []
STATUS_FLOW = ("preparing", "serving", "claimed")


def add_order(invoice_no, order_type, payment_mode, total, summary, cash=0, change_amt=0):
    now = datetime.datetime.now()
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
    orders.append(order)

    if is_online():
        execute(
            """INSERT INTO orders
               (invoice_no, order_type, payment_mode, total, cash, change_amt, status, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,'preparing',%s)""",
            (invoice_no, order_type, payment_mode, total, cash, change_amt, now)
        )
        for name, data in summary.items():
            product_id = data.get("product_id") or None
            execute(
                "INSERT INTO order_lines (invoice_no, name, qty, price, product_id) VALUES (%s,%s,%s,%s,%s)",
                (invoice_no, name, data["qty"], data["price"], product_id)
            )

    push_event("orders", "new-order", {
        "invoice_no":   invoice_no,
        "order_type":   order_type,
        "payment_mode": payment_mode,
        "total":        str(total),
        "status":       "preparing",
    })
    return order


def advance_order(invoice_no):
    for order in orders:
        if order["invoice_no"] == invoice_no:
            idx = STATUS_FLOW.index(order["status"])
            if idx >= len(STATUS_FLOW) - 1:
                return order
            return _set_status(order, STATUS_FLOW[idx + 1])
    return None


def _set_status(order, status):
    order["status"] = status
    now = datetime.datetime.now()
    order[f"{status}_at"] = now.strftime("%I:%M %p")
    if is_online():
        col = f"{status}_at"
        execute(
            f"UPDATE orders SET status=%s, {col}=%s WHERE invoice_no=%s",
            (status, now, order["invoice_no"])
        )
    push_event("orders", "order-updated", {
        "invoice_no": order["invoice_no"],
        "status":     status,
    })
    return order


def get_orders(status=None):
    if not orders and is_online():
        _seed_from_db()
    if status is None:
        return list(orders)
    return [o for o in orders if o["status"] == status]


def _seed_from_db():
    rows = execute(
        """SELECT o.*, ol.name as item_name, ol.qty, ol.price as item_price,
                  COALESCE(oi.cost, 0) as item_cost
           FROM orders o
           JOIN order_lines ol ON o.invoice_no = ol.invoice_no
           LEFT JOIN order_items oi ON ol.product_id = oi.id
           WHERE o.status IN ('preparing','serving')
           ORDER BY o.created_at ASC""",
        fetch="all"
    )
    if not rows:
        return
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
            "qty":    row["qty"],
            "price":  float(row["item_price"]),
            "cost":   float(row["item_cost"]),
            "profit": (float(row["item_price"]) - float(row["item_cost"])) * row["qty"],
        }
    orders.extend(grouped.values())
    print(f"[DB] Seeded {len(grouped)} active orders from MySQL.")
