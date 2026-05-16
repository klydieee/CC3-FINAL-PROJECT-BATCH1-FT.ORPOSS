"""
db/offline_queue.py — Store & Forward queue for ORPOSS.

While the app is offline every mutating operation (add_order, advance_order,
cancel_order, product writes) is serialised as a JSON record and appended to
offline_queue.json next to the .env file.

When the DB comes back online, flush_queue() replays every pending operation
against MySQL in chronological order, then clears the file.

Queue record schema
-------------------
{
  "ts":   "2025-05-16T14:30:00.123456",   # ISO timestamp of original operation
  "op":   "<operation name>",             # one of the OP_* constants below
  "data": { ... }                         # operation-specific payload
}

Operations
----------
  add_order          – insert order + order_lines rows
  advance_order      – bump status to next step in STATUS_FLOW
  cancel_order       – set status = 'cancelled'
  save_stock         – UPDATE order_items SET stock
  save_price         – UPDATE order_items SET price
  save_cost          – UPDATE order_items SET cost
  save_category      – UPDATE order_items SET category
  update_image_url   – UPDATE order_items SET image_url
  set_stock          – UPDATE order_items SET stock  (alias used by restock path)
  add_product        – INSERT INTO order_items
  delete_product     – DELETE FROM order_items
"""

import json
import os
import threading
import datetime

_lock      = threading.Lock()
_QUEUE_FILE = None   # resolved lazily so __file__ is always available


# ── helpers ───────────────────────────────────────────────────────────────────

def _queue_path():
    global _QUEUE_FILE
    if _QUEUE_FILE is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _QUEUE_FILE = os.path.join(base, "offline_queue.json")
    return _QUEUE_FILE


def _load():
    path = _queue_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(records):
    with open(_queue_path(), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)


# ── public API ────────────────────────────────────────────────────────────────

def enqueue(op: str, data: dict):
    """Append one operation to the persistent queue."""
    record = {
        "ts":   datetime.datetime.now().isoformat(),
        "op":   op,
        "data": data,
    }
    with _lock:
        records = _load()
        records.append(record)
        _save(records)
    print(f"[Queue] Stored offline op '{op}' (queue depth: {len(records)})")


def pending_count() -> int:
    return len(_load())


def flush_queue(execute_fn, inventory: dict) -> int:
    """
    Replay all queued operations now that we are online.

    Parameters
    ----------
    execute_fn : callable  – db.connection.execute
    inventory  : dict      – db.products_db.inventory (live dict, mutated in-place)

    Returns the number of operations successfully replayed.
    """
    with _lock:
        records = _load()
        if not records:
            return 0

        replayed = 0
        failed   = []

        for rec in records:
            op   = rec["op"]
            data = rec["data"]
            try:
                _replay(op, data, execute_fn, inventory)
                replayed += 1
                print(f"[Queue] Replayed '{op}' (ts={rec['ts']})")
            except Exception as e:
                print(f"[Queue] FAILED to replay '{op}': {e}")
                failed.append(rec)   # keep for manual inspection

        # Persist only the records that failed (usually empty)
        _save(failed)
        if not failed:
            print(f"[Queue] Flush complete — {replayed} op(s) synced, queue cleared.")
        else:
            print(f"[Queue] Flush partial — {replayed} synced, {len(failed)} failed (kept).")
        return replayed


# ── replay logic ──────────────────────────────────────────────────────────────

def _replay(op, data, execute_fn, inventory):
    import datetime as _dt

    STATUS_FLOW = ("preparing", "serving", "claimed")

    if op == "add_order":
        # Re-insert order — skip gracefully if invoice already exists (duplicate flush)
        try:
            execute_fn(
                """INSERT INTO orders
                   (invoice_no, order_type, payment_mode, total, cash, change_amt, status, created_at)
                   VALUES (%s,%s,%s,%s,%s,%s,'preparing',%s)""",
                (
                    data["invoice_no"],
                    data["order_type"],
                    data["payment_mode"],
                    data["total"],
                    data.get("cash", 0),
                    data.get("change_amt", 0),
                    data.get("created_at", _dt.datetime.now()),
                )
            )
        except Exception as e:
            if "Duplicate" in str(e) or "duplicate" in str(e):
                print(f"[Queue]   ↳ order {data['invoice_no']} already exists, skipping insert.")
            else:
                raise
        for name, item in data.get("summary", {}).items():
            try:
                execute_fn(
                    "INSERT INTO order_lines (invoice_no, name, qty, price, product_id) VALUES (%s,%s,%s,%s,%s)",
                    (data["invoice_no"], name, item["qty"], item["price"], item.get("product_id"))
                )
            except Exception as e:
                if "Duplicate" not in str(e):
                    raise

    elif op == "advance_order":
        row = execute_fn(
            "SELECT status FROM orders WHERE invoice_no=%s",
            (data["invoice_no"],), fetch="one"
        )
        if not row:
            print(f"[Queue]   ↳ order {data['invoice_no']} not found, skipping advance.")
            return
        current = row["status"]
        if current not in STATUS_FLOW:
            return
        idx = STATUS_FLOW.index(current)
        if idx >= len(STATUS_FLOW) - 1:
            return
        new_status = STATUS_FLOW[idx + 1]
        now = _dt.datetime.now()
        execute_fn(
            f"UPDATE orders SET status=%s, {new_status}_at=%s WHERE invoice_no=%s",
            (new_status, now, data["invoice_no"])
        )

    elif op == "cancel_order":
        execute_fn(
            "UPDATE orders SET status='cancelled' WHERE invoice_no=%s AND status='preparing'",
            (data["invoice_no"],)
        )

    elif op in ("save_stock", "set_stock"):
        item = inventory.get(data["name"])
        if item and item.get("id"):
            execute_fn(
                "UPDATE order_items SET stock=%s WHERE id=%s",
                (data["stock"], item["id"])
            )

    elif op == "save_price":
        item = inventory.get(data["name"])
        if item and item.get("id"):
            execute_fn(
                "UPDATE order_items SET price=%s WHERE id=%s",
                (data["price"], item["id"])
            )

    elif op == "save_cost":
        item = inventory.get(data["name"])
        if item and item.get("id"):
            execute_fn(
                "UPDATE order_items SET cost=%s WHERE id=%s",
                (data["cost"], item["id"])
            )

    elif op == "save_category":
        item = inventory.get(data["name"])
        if item and item.get("id"):
            execute_fn(
                "UPDATE order_items SET category=%s WHERE id=%s",
                (data["category"], item["id"])
            )

    elif op == "update_image_url":
        item = inventory.get(data["name"])
        if item and item.get("id"):
            execute_fn(
                "UPDATE order_items SET image_url=%s WHERE id=%s",
                (data["image_url"], item["id"])
            )

    elif op == "add_product":
        try:
            new_id = execute_fn(
                "INSERT INTO order_items (name, price, stock, cost, category) VALUES (%s,%s,%s,%s,%s)",
                (data["name"], data["price"], data["stock"], data["cost"], data["category"])
            )
            if data["name"] in inventory:
                inventory[data["name"]]["id"] = new_id
        except Exception as e:
            if "Duplicate" in str(e) or "duplicate" in str(e):
                print(f"[Queue]   ↳ product '{data['name']}' already exists, skipping insert.")
            else:
                raise

    elif op == "delete_product":
        item = inventory.get(data["name"])
        if item and item.get("id"):
            execute_fn("DELETE FROM order_items WHERE id=%s", (item["id"],))

    else:
        print(f"[Queue]   ↳ Unknown op '{op}', skipping.")
