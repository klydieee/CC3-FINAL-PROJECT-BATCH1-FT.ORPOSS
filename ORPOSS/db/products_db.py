"""
db/products_db.py
Loads inventory from MySQL order_items (the product catalog).
Falls back to data/inventory.py if offline.
Fires Pusher 'inventory-updated' event on any change so all laptops sync live.
All mutating ops that run while offline are queued for later sync.
"""
from db.connection    import execute, is_online
from db.offline_queue import enqueue
from data.inventory   import inventory as _local_inventory
from utils.pusher_client import push_event

inventory = {}


def load_inventory():
    global inventory
    if is_online():
        rows = execute(
            "SELECT id, name, price, stock, image_url, cost, category FROM order_items",
            fetch="all"
        )
        if rows:
            inventory.clear()
            for row in rows:
                inventory[row["name"]] = {
                    "id":        row["id"],
                    "price":     float(row["price"]),
                    "stock":     row["stock"],
                    "image_url": row["image_url"] or "",
                    "cost":      float(row.get("cost", 0)),
                    "category":  row.get("category") or "All",
                }
            print(f"[DB] Loaded {len(inventory)} products from order_items.")
            return
    print("[DB] Offline — using local inventory.py")
    inventory.clear()
    inventory.update({
        k: {
            "id":        None,
            "price":     v["price"],
            "stock":     v["stock"],
            "cost":      v.get("cost", 0),
            "image_url": "",
            "category":  v.get("category", "All"),
        }
        for k, v in _local_inventory.items()
    })


def _push_inventory():
    push_event("inventory", "inventory-updated", {
        "items": {
            name: {
                "price":     item["price"],
                "stock":     item["stock"],
                "image_url": item["image_url"],
                "cost":      item.get("cost", 0),
                "category":  item.get("category", "All"),
            }
            for name, item in inventory.items()
        }
    })


def save_stock(name):
    item = inventory.get(name)
    if not item:
        return
    if item.get("id") and is_online():
        execute("UPDATE order_items SET stock=%s WHERE id=%s", (item["stock"], item["id"]))
        _push_inventory()
    elif not is_online():
        enqueue("save_stock", {"name": name, "stock": item["stock"]})


def save_price(name, price):
    if name in inventory:
        inventory[name]["price"] = price
    item = inventory.get(name)
    if not item:
        return
    if item.get("id") and is_online():
        execute("UPDATE order_items SET price=%s WHERE id=%s", (price, item["id"]))
        _push_inventory()
    elif not is_online():
        enqueue("save_price", {"name": name, "price": price})


def set_stock(name, stock):
    item = inventory.get(name)
    if item is None:
        return
    item["stock"] = stock
    if item.get("id") and is_online():
        execute("UPDATE order_items SET stock=%s WHERE id=%s", (stock, item["id"]))
        _push_inventory()
    elif not is_online():
        enqueue("set_stock", {"name": name, "stock": stock})


def restock_all(amount=100):
    for name, item in inventory.items():
        item["stock"] += amount
        if item.get("id") and is_online():
            execute("UPDATE order_items SET stock=%s WHERE id=%s",
                    (item["stock"], item["id"]))
        elif not is_online():
            enqueue("set_stock", {"name": name, "stock": item["stock"]})
    _push_inventory()


def save_cost(name, cost):
    if name in inventory:
        inventory[name]["cost"] = cost
    item = inventory.get(name)
    if not item:
        return
    if item.get("id") and is_online():
        execute("UPDATE order_items SET cost=%s WHERE id=%s", (cost, item["id"]))
        _push_inventory()
    elif not is_online():
        enqueue("save_cost", {"name": name, "cost": cost})


def update_image_url(name, image_url):
    item = inventory.get(name)
    if item is None:
        return
    item["image_url"] = image_url
    if item.get("id") and is_online():
        execute("UPDATE order_items SET image_url=%s WHERE id=%s",
                (image_url, item["id"]))
        _push_inventory()
    elif not is_online():
        enqueue("update_image_url", {"name": name, "image_url": image_url})


def add_product(name, price, stock=50, cost=0, category="All"):
    """Add a new product. Returns (True, msg) on success."""
    if name in inventory:
        return False, "Product already exists."
    new_id = None
    if is_online():
        new_id = execute(
            "INSERT INTO order_items (name, price, stock, cost, category) VALUES (%s,%s,%s,%s,%s)",
            (name, price, stock, cost, category)
        )
    else:
        enqueue("add_product", {
            "name": name, "price": price,
            "stock": stock, "cost": cost, "category": category,
        })
    inventory[name] = {
        "id":        new_id,
        "price":     float(price),
        "stock":     stock,
        "cost":      float(cost),
        "image_url": "",
        "category":  category,
    }
    _push_inventory()
    return True, "Product added."


def save_category(name, category):
    item = inventory.get(name)
    if item is None:
        return
    item["category"] = category
    if item.get("id") and is_online():
        execute("UPDATE order_items SET category=%s WHERE id=%s",
                (category, item["id"]))
        _push_inventory()
    elif not is_online():
        enqueue("save_category", {"name": name, "category": category})


def delete_product(name):
    """Remove a product. Returns (True, msg) on success."""
    item = inventory.get(name)
    if not item:
        return False, "Product not found."
    if item.get("id") and is_online():
        execute("DELETE FROM order_items WHERE id=%s", (item["id"],))
    elif not is_online():
        enqueue("delete_product", {"name": name})
    del inventory[name]
    _push_inventory()
    return True, "Product deleted."
