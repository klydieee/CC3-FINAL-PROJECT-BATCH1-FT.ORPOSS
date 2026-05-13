import datetime

from utils.palette import palette


orders = []
STATUS_FLOW = ("preparing", "serving", "claimed")


def add_order(invoice_no, order_type, payment_mode, total, summary):
    order = {
        "invoice_no": invoice_no,
        "order_type": order_type,
        "payment_mode": payment_mode,
        "total": total,
        "summary": summary,
        "status": "preparing",
        "created_at": datetime.datetime.now().strftime("%I:%M %p"),
        "serving_at": "",
        "claimed_at": "",
    }
    # keep the first order at the top >>
    orders.append(order)
    return order


def mark_serving(invoice_no):
    return set_order_status(invoice_no, "serving")


def mark_claimed(invoice_no):
    return set_order_status(invoice_no, "claimed")


def set_order_status(invoice_no, status):
    if status not in STATUS_FLOW:
        return None

    for order in orders:
        if order["invoice_no"] == invoice_no:
            order["status"] = status
            order[f"{status}_at"] = datetime.datetime.now().strftime("%I:%M %p")
            return order
    return None


def advance_order(invoice_no):
    for order in orders:
        if order["invoice_no"] == invoice_no:
            current_index = STATUS_FLOW.index(order["status"])
            if current_index >= len(STATUS_FLOW) - 1:
                return order
            return set_order_status(invoice_no, STATUS_FLOW[current_index + 1])
    return None


def get_orders(status=None):
    if status is None:
        return list(orders)
    return [order for order in orders if order["status"] == status]