"""
db/products_db.py
Loads inventory from MySQL order_items (the product catalog).
Falls back to data/inventory.py if offline.
Fires Pusher 'inventory-updated' event on any change so all laptops sync live.
"""
from db.connection import execute, is_online
from data.inventory import inventory as _local_inventory
from utils.pusher_client import push_event

inventory = {}


def load_inventory():
    global inventory
    if is_online():
        rows = execute(
            "SELECT id, name, price, stock, image_url FROM order_items",
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
                }
            print(f"[DB] Loaded {len(inventory)} products from order_items.")
            return
    print("[DB] Offline -- using local inventory.py")
    inventory.clear()
    inventory.update({
        k: {"id": None, "price": v["price"], "stock": v["stock"], "image_url": ""}
        for k, v in _local_inventory.items()
    })


def _push_inventory():
    """Notify all clients that inventory has changed — they should reload."""
    push_event("inventory", "inventory-updated", {
        "items": {
            name: {
                "price":     item["price"],
                "stock":     item["stock"],
                "image_url": item["image_url"],
            }
            for name, item in inventory.items()
        }
    })


def save_stock(name):
    item = inventory.get(name)
    if item and item.get("id") and is_online():
        execute("UPDATE order_items SET stock=%s WHERE id=%s",
                (item["stock"], item["id"]))
        _push_inventory()


def save_price(name, price):
    if name in inventory:
        inventory[name]["price"] = price
    item = inventory.get(name)
    if item and item.get("id") and is_online():
        execute("UPDATE order_items SET price=%s WHERE id=%s",
                (price, item["id"]))
        _push_inventory()


def set_stock(name, stock):
    item = inventory.get(name)
    if item is not None:
        item["stock"] = stock
        if item.get("id") and is_online():
            execute("UPDATE order_items SET stock=%s WHERE id=%s",
                    (stock, item["id"]))
            _push_inventory()


def restock_all(amount=100):
    for name, item in inventory.items():
        item["stock"] += amount
        if item.get("id") and is_online():
            execute("UPDATE order_items SET stock=%s WHERE id=%s",
                    (item["stock"], item["id"]))
    _push_inventory()


def update_image_url(name, image_url):
    item = inventory.get(name)
    if item is not None:
        item["image_url"] = image_url
        if item.get("id") and is_online():
            execute("UPDATE order_items SET image_url=%s WHERE id=%s",
                    (image_url, item["id"]))
            _push_inventory()


def add_product(name, price, stock=50):
    """Add a new product to DB and local inventory. Returns True on success."""
    if name in inventory:
        return False, "Product already exists."
    new_id = None
    if is_online():
        new_id = execute(
            "INSERT INTO order_items (name, price, stock) VALUES (%s, %s, %s)",
            (name, price, stock)
        )
    inventory[name] = {"id": new_id, "price": float(price), "stock": stock, "image_url": ""}
    _push_inventory()
    return True, "Product added."


def delete_product(name):
    """Remove a product from DB and local inventory. Returns True on success."""
    item = inventory.get(name)
    if not item:
        return False, "Product not found."
    if item.get("id") and is_online():
        execute("DELETE FROM order_items WHERE id=%s", (item["id"],))
    del inventory[name]
    _push_inventory()
    return True, "Product deleted."
