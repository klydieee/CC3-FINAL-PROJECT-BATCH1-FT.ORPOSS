import tkinter as tk
from tkinter import messagebox, ttk
import os
import re

from datetime import datetime, timedelta
from data.inventory import inventory
from utils.helper import peso

def start_admin_panel(window, back_to_pos_callback):
    # Clear window for Admin view
    for widget in window.winfo_children():
        widget.destroy()

    # --- Theme Configuration ---
    BG_COLOR = "#f8f9fa"
    SIDEBAR_COLOR = "#2c3e50"
    TEXT_COLOR = "#2c3e50"
    PRIMARY_COLOR = "#3498db"
    SECONDARY_COLOR = "#2ecc71"
    ACCENT_COLOR = "#e74c3c"
    PURPLE_COLOR = "#9b59b6"
    WARNING_COLOR = "#f39c12"

    BTN_FONT = ("Segoe UI", 10, "bold")
    BTN_PAD_Y = 12

    window.configure(bg=BG_COLOR)

    # --- Sidebar ---
    sidebar = tk.Frame(window, bg=SIDEBAR_COLOR, width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="ADMIN\nSYSTEM", fg="white", bg=SIDEBAR_COLOR,
             font=("Segoe UI", 16, "bold"), pady=40).pack()

    tk.Button(sidebar, text="RETURN TO POS", bg=ACCENT_COLOR, fg="white", relief="flat",
              font=BTN_FONT, cursor="hand2", command=back_to_pos_callback).pack(side="bottom", fill="x", padx=15,
                                                                                pady=30)

    # --- Main Content Area ---
    main_content = tk.Frame(window, bg=BG_COLOR)
    main_content.pack(side="left", fill="both", expand=True, padx=40, pady=40)

    # 1. INVENTORY TABLE SECTION
    inv_frame = tk.LabelFrame(main_content, text=" Inventory Management ", font=BTN_FONT,
                              padx=20, pady=20, bg="white", fg=TEXT_COLOR, relief="flat")
    inv_frame.pack(side="left", fill="both", expand=True)

    # Table Setup
    tree = ttk.Treeview(inv_frame, columns=("name", "price", "stock"), show="headings", selectmode="extended")
    tree.heading("name", text="ITEM NAME")
    tree.heading("price", text="UNIT PRICE")
    tree.heading("stock", text="STOCK COUNT")

    tree.column("name", width=250, anchor="w")
    tree.column("price", width=120, anchor="center")
    tree.column("stock", width=120, anchor="center")

    # NEW: Table Tags for Colors
    tree.tag_configure("lowstock", background="#ff7675", foreground="white")
    tree.pack(fill="both", expand=True)

    def save_to_disk():
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        inv_file = os.path.join(base_path, "data", "inventory.py")
        with open(inv_file, "w") as f:
            f.write(f"inventory = {repr(inventory)}")

    def refresh_table(filter_low=False):
        for i in tree.get_children(): tree.delete(i)
        low_count = 0
        for name, data in inventory.items():
            stock = data['stock']
            tag = "lowstock" if stock < 10 else ""
            if stock < 10: low_count += 1

            if filter_low and stock >= 10:
                continue

            tree.insert("", "end", values=(name.upper(), peso(data['price']), stock), tags=(tag,))
        return low_count

    # --- SALES HISTORY LOGIC ---
    def open_history_log():
        log_win = tk.Toplevel(window)
        log_win.title("Transaction History")
        log_win.geometry("700x850")
        log_win.configure(bg=BG_COLOR)
        log_win.grab_set()

        count_var = tk.StringVar(value="1")
        unit_var = tk.StringVar(value="Days")
        receipt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "receipts")

        header = tk.Frame(log_win, bg="white", pady=20, padx=30)
        header.pack(fill="x")
        tk.Label(header, text="Sales History Log", font=("Segoe UI", 18, "bold"), bg="white", fg=SIDEBAR_COLOR).pack(
            side="left")

        summary_card = tk.Frame(log_win, bg=SECONDARY_COLOR, padx=20, pady=15)
        summary_card.pack(fill="x", padx=30, pady=20)
        summary_lbl = tk.Label(summary_card, text="Total: ₱0.00", font=("Segoe UI", 14, "bold"), bg=SECONDARY_COLOR,
                               fg="white")
        summary_lbl.pack()

        filter_bar = tk.Frame(log_win, bg="white", padx=20, pady=15)
        filter_bar.pack(fill="x", padx=30, pady=(0, 20))
        tk.Label(filter_bar, text="Filter Past:", bg="white").pack(side="left", padx=5)
        tk.Entry(filter_bar, textvariable=count_var, width=5, justify="center").pack(side="left", padx=5)
        ttk.Combobox(filter_bar, textvariable=unit_var, values=["Hours", "Days", "Months", "All Time"],
                     state="readonly", width=12).pack(side="left", padx=5)

        def render_logs():
            for widget in scroll_frame.winfo_children(): widget.destroy()
            total = 0.0
            now = datetime.now()
            try:
                val = int(count_var.get())
                unit = unit_var.get()
                if unit == "Hours":
                    limit = now - timedelta(hours=val)
                elif unit == "Days":
                    limit = now - timedelta(days=val)
                elif unit == "Months":
                    limit = now - timedelta(days=val * 30)
                else:
                    limit = datetime.min
            except:
                limit = datetime.min

            if os.path.exists(receipt_dir):
                files = sorted([f for f in os.listdir(receipt_dir) if f.endswith(".txt")], reverse=True)
                for file_name in files:
                    try:
                        ts = re.sub(r'\D', '', file_name)
                        if len(ts) < 14: continue
                        if datetime.strptime(ts[:14], "%Y%m%d%H%M%S") >= limit:
                            with open(os.path.join(receipt_dir, file_name), "r", encoding="utf-8") as f:
                                content = f.read()
                                match = re.search(r'TOTAL:\s*₱?([\d,.]+)', content)
                                if match: total += float(match.group(1).replace(',', ''))
                            btn = tk.Button(scroll_frame, text=f"  🧾  {file_name}", font=("Segoe UI Semibold", 10),
                                            anchor="w", bg="white", relief="flat", pady=12, padx=15,
                                            command=lambda f=file_name: open_raw_file(f))
                            btn.pack(fill="x", pady=2)
                    except:
                        continue
            summary_lbl.config(text=f"Total Revenue (Last {count_var.get()} {unit}): {peso(total)}")

        tk.Button(filter_bar, text="APPLY", command=render_logs, bg=PRIMARY_COLOR, fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=15).pack(side="left", padx=10)

        list_container = tk.Frame(log_win, bg="white")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=620)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True);
        scrollbar.pack(side="right", fill="y")

        def open_raw_file(filename):
            file_win = tk.Toplevel(log_win)
            file_win.title(f"Receipt: {filename}")
            file_win.geometry("400x600")
            txt_area = tk.Text(file_win, font=("Consolas", 11), padx=30, pady=30, bg="#fdfdfd", relief="flat")
            txt_area.pack(fill="both", expand=True)
            with open(os.path.join(receipt_dir, filename), "r", encoding="utf-8") as f:
                txt_area.insert(tk.END, f.read())
            txt_area.config(state="disabled")

        render_logs()

    # 2. CONTROL PANEL (Right Side)
    control_panel = tk.Frame(main_content, bg=BG_COLOR, width=300)
    control_panel.pack(side="right", fill="y", padx=(40, 0))
    control_panel.pack_propagate(False)

    top_actions = tk.Frame(control_panel, bg=BG_COLOR)
    top_actions.pack(side="top", fill="both", expand=True)

    # Edit Section
    edit_frame = tk.LabelFrame(top_actions, text=" Edit Selection ", bg="white", padx=20, pady=20, font=BTN_FONT,
                               relief="flat")
    edit_frame.pack(fill="x", pady=(0, 20))

    tk.Label(edit_frame, text="New Price (₱):", bg="white").pack(anchor="w")
    price_entry = tk.Entry(edit_frame, justify="center", font=("Segoe UI", 12), bg=BG_COLOR, relief="flat")
    price_entry.pack(fill="x", pady=(5, 15), ipady=8)

    tk.Label(edit_frame, text="New Stock Level:", bg="white").pack(anchor="w")
    stock_entry = tk.Entry(edit_frame, justify="center", font=("Segoe UI", 12), bg=BG_COLOR, relief="flat")
    stock_entry.pack(fill="x", pady=(5, 15), ipady=8)

    def save_edits():
        selected = tree.selection()
        if not selected: return messagebox.showwarning("Selection", "Select items first.")
        try:
            p = float(price_entry.get()) if price_entry.get() else None
            s = int(stock_entry.get()) if stock_entry.get() else None
            for item_id in selected:
                name = tree.item(item_id)['values'][0]
                key = next((k for k in inventory if k.upper() == name), name)
                if p is not None: inventory[key]['price'] = p
                if s is not None: inventory[key]['stock'] = s
            save_to_disk();
            refresh_table()
            price_entry.delete(0, tk.END);
            stock_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Inventory Updated.")
        except:
            messagebox.showerror("Error", "Invalid input.")

    tk.Button(edit_frame, text="SAVE CHANGES", bg=SECONDARY_COLOR, fg="white", font=BTN_FONT,
              relief="flat", pady=BTN_PAD_Y, cursor="hand2", command=save_edits).pack(fill="x")

    # Bulk Section
    maint_frame = tk.LabelFrame(top_actions, text=" Inventory Tools ", bg="white", padx=20, pady=20, font=BTN_FONT,
                                relief="flat")
    maint_frame.pack(fill="x", pady=(0, 20))

    # NEW: Filter Buttons for Low Stock
    tk.Button(maint_frame, text="SHOW ALL ITEMS", bg=SIDEBAR_COLOR, fg="white", font=("Segoe UI", 9, "bold"),
              relief="flat", pady=8, command=lambda: refresh_table(False)).pack(fill="x", pady=(0, 5))

    tk.Button(maint_frame, text="SHOW LOW STOCK", bg=WARNING_COLOR, fg="white", font=("Segoe UI", 9, "bold"),
              relief="flat", pady=8, command=lambda: refresh_table(True)).pack(fill="x", pady=(0, 15))

    def restock_all():
        if messagebox.askyesno("Restock All", "Add 100 units to all items?"):
            for item in inventory: inventory[item]['stock'] = inventory[item]['stock'] + 100
            save_to_disk();
            refresh_table()

    tk.Button(maint_frame, text="RESTOCK ALL (100)", bg=PURPLE_COLOR, fg="white", font=BTN_FONT,
              relief="flat", pady=BTN_PAD_Y, cursor="hand2", command=restock_all).pack(fill="x")

    # Bottom Reports Section
    reports_frame = tk.Frame(control_panel, bg=BG_COLOR)
    reports_frame.pack(side="bottom", fill="x")

    tk.Label(reports_frame, text="Reports & Logs", font=BTN_FONT, bg=BG_COLOR, fg=SIDEBAR_COLOR).pack(anchor="w",
                                                                                                      pady=(0, 5))

    tk.Button(reports_frame, text="VIEW SALES HISTORY", bg=PRIMARY_COLOR, fg="white", font=BTN_FONT,
              relief="flat", pady=BTN_PAD_Y, cursor="hand2", command=open_history_log).pack(fill="x")

    # Initial Table Load & Alert
    low_stock_found = refresh_table()
    if low_stock_found > 0:
        messagebox.showwarning("Inventory Alert", f"There are {low_stock_found} items with low stock (<10)!")