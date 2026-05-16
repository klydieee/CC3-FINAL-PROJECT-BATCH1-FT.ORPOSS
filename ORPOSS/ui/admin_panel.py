import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import re
import threading

from datetime import datetime, timedelta
from db.products_db import inventory, update_image_url
from utils.helper import peso
from utils.image_storage import ImageStorage
from ui.order_status_window import open_order_status_window
from ui.window_utils import clear_main_window
from utils.palette import palette


def start_admin_panel(window, back_to_pos_callback):
    clear_main_window(window)

    BTN_FONT  = ("Segoe UI", 10, "bold")
    BTN_PAD_Y = 12

    window.configure(bg=palette.bg)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    sidebar = tk.Frame(window, bg=palette.text, width=180)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    tk.Label(sidebar, text="ADMIN\nSYSTEM", fg="white", bg=palette.text,
             font=("Segoe UI", 16, "bold"), pady=40).pack()

    tk.Button(sidebar, text="RETURN TO LAUNCHER", bg=palette.danger, fg="white", relief="flat",
              font=BTN_FONT, cursor="hand2", command=back_to_pos_callback).pack(
              side="bottom", fill="x", padx=15, pady=30)

    # ── Main Content ──────────────────────────────────────────────────────────
    main_content = tk.Frame(window, bg=palette.bg)
    main_content.pack(side="left", fill="both", expand=True, padx=40, pady=40)

    # Left: Inventory table
    inv_frame = tk.LabelFrame(main_content, text=" Inventory Management ", font=BTN_FONT,
                          padx=20, pady=20, bg="white", fg=palette.text, relief="flat")
    inv_frame.pack(side="left", fill="both", expand=True)

    # 1. Added "cost" to columns
    tree = ttk.Treeview(inv_frame, columns=("name", "price", "cost", "stock", "category"), show="headings", selectmode="extended")
    tree.heading("name",     text="ITEM NAME")
    tree.heading("price",    text="UNIT PRICE")
    tree.heading("cost",     text="UNIT COST")
    tree.heading("stock",    text="STOCK COUNT")
    tree.heading("category", text="CATEGORY")

    tree.column("name",     width=180, anchor="w")
    tree.column("price",    width=90,  anchor="center")
    tree.column("cost",     width=90,  anchor="center")
    tree.column("stock",    width=90,  anchor="center")
    tree.column("category", width=110, anchor="center")

    # Visual tags for the Admin
    tree.tag_configure("lowstock", background="#ff7675", foreground="white")
    tree.tag_configure("lowmargin", background="#ffeaa7") # Pale yellow for low profit
    tree.pack(fill="both", expand=True)

    def save_to_disk():
        """Only writes to inventory.py when offline — DB handles persistence when online."""
        from db.connection import is_online
        if not is_online():
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            inv_file  = os.path.join(base_path, "data", "inventory.py")
            with open(inv_file, "w") as f:
                f.write(f"inventory = {repr(inventory)}")

    def refresh_table(filter_low=False):
        for i in tree.get_children():
            tree.delete(i)
        
        low_count = 0
        # Assuming inventory is a dict: {name: {'price': 0, 'cost': 0, 'stock': 0}}
        for name, data in inventory.items():
            stock = data['stock']
            price = data['price']
            cost  = data.get('cost', 0) # Use .get() in case cost isn't set yet
            profit = price - cost
            
            # Determine Tags
            tags = []
            if stock < 10:
                low_count += 1
                tags.append("lowstock")
            
            # Highlight if profit is thin (less than 5)
            if profit < 5:
                tags.append("lowmargin")
                
            if filter_low and stock >= 10:
                continue
                
            # Insert into tree with all 5 columns: Name, Price, Cost, Stock, Category
            cat = data.get("category", "All")
            tree.insert("", "end",
                        values=(name.upper(), peso(price), peso(cost), stock, cat),
                        tags=tuple(tags))
                        
        return low_count

    # ── Sales History popup ───────────────────────────────────────────────────
    def open_history_log():
        log_win = tk.Toplevel(window)
        log_win.title("Transaction History")
        log_win.geometry("700x850")
        log_win.configure(bg=palette.bg)
        log_win.grab_set()

        count_var   = tk.StringVar(value="1")
        unit_var    = tk.StringVar(value="Days")
        receipt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "receipts")

        header = tk.Frame(log_win, bg="white", pady=20, padx=30)
        header.pack(fill="x")
        tk.Label(header, text="Sales & Profit Log", font=("Segoe UI", 18, "bold"),
                 bg="white", fg=palette.text).pack(side="left")

        # UPDATED: Summary card now shows both Revenue and Profit
        summary_card = tk.Frame(log_win, bg=palette.secondary, padx=20, pady=15)
        summary_card.pack(fill="x", padx=30, pady=20)

        filter_bar = tk.Frame(log_win, bg="white", padx=20, pady=15)
        filter_bar.pack(fill="x", padx=30, pady=(0, 20))
        tk.Label(filter_bar, text="Filter Past:", bg="white").pack(side="left", padx=5)
        tk.Entry(filter_bar, textvariable=count_var, width=5, justify="center").pack(side="left", padx=5)
        ttk.Combobox(filter_bar, textvariable=unit_var,
                     values=["Hours", "Days", "Months", "All Time"],
                     state="readonly", width=12).pack(side="left", padx=5)
        # Simple fuzzy search for receipt filenames
        tk.Label(filter_bar, text="Search:", bg="white").pack(side="left", padx=(12, 4))
        search_var = tk.StringVar(value="")
        search_entry = tk.Entry(filter_bar, textvariable=search_var, width=25)
        search_entry.pack(side="left", padx=5)

        def fuzzy_match(name, query):
            if not query:
                return True
            s = re.sub(r'\W', '', name).lower()
            q = re.sub(r'\W', '', query).lower()
            i = 0
            for ch in q:
                i = s.find(ch, i)
                if i == -1:
                    return False
                i += 1
            return True

        def render_logs():
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            total_rev = 0.0
            total_profit = 0.0
            search_q = search_var.get().strip()
            now = datetime.now()
            
            try:
                val = int(count_var.get())
                unit = unit_var.get()
                if unit == "Hours": limit = now - timedelta(hours=val)
                elif unit == "Days": limit = now - timedelta(days=val)
                elif unit == "Months": limit = now - timedelta(days=val * 30)
                else: limit = datetime.min
            except:
                limit = datetime.min

            if os.path.exists(receipt_dir):
                files = sorted([f for f in os.listdir(receipt_dir) if f.endswith(".txt")], reverse=True)
                for file_name in files:
                    try:
                        # Extract timestamp from filename (e.g., 20231025123000.txt)
                        ts_str = re.sub(r'\D', '', file_name)
                        if len(ts_str) < 14: continue
                        
                        file_dt = datetime.strptime(ts_str[:14], "%Y%m%d%H%M%S")
                        
                        if file_dt >= limit:
                            # Filter by fuzzy search on the filename
                            if search_q and not fuzzy_match(file_name, search_q):
                                continue
                            with open(os.path.join(receipt_dir, file_name), "r", encoding="utf-8") as f:
                                content = f.read()
                                # Parse Revenue
                                rev_match = re.search(r'TOTAL:\s*₱?([\d,.]+)', content)
                                if rev_match:
                                    total_rev += float(rev_match.group(1).replace(',', ''))

                                # Parse PROFIT tag if present (receipts generated after the feature was added)
                                profit_match = re.search(r'PROFIT:\s*₱?([\d,.]+)', content)
                                if profit_match:
                                    total_profit += float(profit_match.group(1).replace(',', ''))
                                else:
                                    # Fallback: estimate profit from line items using current inventory costs
                                    for line in content.splitlines():
                                        m = re.match(r'^(.+?)\s+(\d+)x\s+₱([\d,.]+)', line)
                                        if m:
                                            item_name = m.group(1).strip()
                                            qty = int(m.group(2))
                                            # Look up cost from current inventory (best-effort)
                                            key = next((k for k in inventory if k.upper() == item_name.upper()), None)
                                            if key:
                                                price = inventory[key]["price"]
                                                cost  = inventory[key].get("cost", 0) or 0
                                                total_profit += (price - cost) * qty

                            btn = tk.Button(scroll_frame, text=f"  🧾  {file_name}",
                                            font=("Segoe UI Semibold", 10), anchor="w",
                                            bg="white", relief="flat", pady=12, padx=15,
                                            command=lambda fn=file_name: open_raw_file(fn))
                            btn.pack(fill="x", pady=2)
                    except:
                        continue

        tk.Button(filter_bar, text="APPLY", command=render_logs,
                  bg=palette.primary, fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=15).pack(side="left", padx=10)

        list_container = tk.Frame(log_win, bg="white")
        list_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=620)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def open_raw_file(filename):
            file_win = tk.Toplevel(log_win)
            file_win.title(f"Receipt: {filename}")
            file_win.geometry("400x600")
            txt_area = tk.Text(file_win, font=("Consolas", 11), padx=30, pady=30,
                               bg="#fdfdfd", relief="flat")
            txt_area.pack(fill="both", expand=True)
            with open(os.path.join(receipt_dir, filename), "r", encoding="utf-8") as f:
                txt_area.insert(tk.END, f.read())
            txt_area.config(state="disabled")

        render_logs()

    # ── Sales Analytics chart popup ───────────────────────────────────────────
    def open_sales_chart():
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            messagebox.showerror("Missing Library",
                                 "matplotlib is not installed.\nRun: pip install matplotlib")
            return

        chart_win = tk.Toplevel(window)
        chart_win.title("Sales Analytics")
        chart_win.geometry("900x620")
        chart_win.configure(bg=palette.bg)
        chart_win.grab_set()

        # ── Controls row ──────────────────────────────────────────────────────
        ctrl = tk.Frame(chart_win, bg="white", pady=12, padx=20)
        ctrl.pack(fill="x")

        tk.Label(ctrl, text="Sales Analytics", font=("Segoe UI", 14, "bold"),
                 bg="white", fg=palette.text).pack(side="left", padx=(0, 20))

        period_var = tk.StringVar(value="Daily")
        periods    = ["Daily", "Weekly", "Monthly", "Quarterly", "Bi-Annual", "Yearly"]

        def make_period_btn(label):
            def _cmd():
                period_var.set(label)
                for b in period_btns:
                    b.config(bg="white", fg=palette.text)
                period_btns[periods.index(label)].config(bg=palette.primary, fg="white")
                render_chart()
            return _cmd

        period_btns = []
        btn_row = tk.Frame(ctrl, bg="white")
        btn_row.pack(side="left")
        for p in periods:
            b = tk.Button(btn_row, text=p, font=("Segoe UI", 9, "bold"),
                          bg=palette.primary if p == "Daily" else "white",
                          fg="white" if p == "Daily" else palette.text,
                          relief="flat", padx=10, pady=6, cursor="hand2",
                          command=make_period_btn(p))
            b.pack(side="left", padx=2)
            period_btns.append(b)

        # Manual refresh only — no auto-polling
        tk.Button(btn_row, text="⟳  Refresh", font=("Segoe UI", 9, "bold"),
                  bg="#f39c12", fg="white", relief="flat", padx=10, pady=6,
                  cursor="hand2", command=lambda: render_chart()
                  ).pack(side="left", padx=(12, 0))

        # ── Chart area ────────────────────────────────────────────────────────
        chart_frame = tk.Frame(chart_win, bg=palette.bg)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

        fig, ax = plt.subplots(figsize=(8.5, 4.5))
        fig.patch.set_facecolor(palette.bg)
        canvas_widget = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas_widget.get_tk_widget().pack(fill="both", expand=True)

        def load_orders_from_db():
            """Query orders + order_lines joined to order_items for cost — all terminals, real data."""
            from db.connection import execute
            rows = execute(
                """SELECT o.created_at, o.total,
                          COALESCE(SUM((ol.price - COALESCE(oi.cost, 0)) * ol.qty), 0) AS profit
                   FROM `orders` o
                   LEFT JOIN `order_lines` ol ON o.invoice_no = ol.invoice_no
                   LEFT JOIN `order_items` oi ON ol.product_id = oi.id
                   GROUP BY o.id, o.created_at, o.total""",
                fetch="all"
            )
            if not rows:
                return []
            result = []
            for row in rows:
                dt     = row["created_at"]
                amt    = float(row["total"])
                profit = float(row["profit"])
                if isinstance(dt, str):
                    try:
                        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue
                result.append((dt, amt, profit))
            return result

        def bucket_key(dt, period):
            if period == "Daily":
                return dt.strftime("%Y-%m-%d")
            elif period == "Weekly":
                return dt.strftime("%Y-W%W")
            elif period == "Monthly":
                return dt.strftime("%Y-%m")
            elif period == "Quarterly":
                q = (dt.month - 1) // 3 + 1
                return f"{dt.year}-Q{q}"
            elif period == "Bi-Annual":
                h = 1 if dt.month <= 6 else 2
                return f"{dt.year}-H{h}"
            else:
                return str(dt.year)

        def render_chart():
            from collections import defaultdict
            import numpy as np
            period   = period_var.get()
            raw      = load_orders_from_db()
            rev_buckets    = defaultdict(float)
            profit_buckets = defaultdict(float)
            for dt, amt, profit in raw:
                key = bucket_key(dt, period)
                rev_buckets[key]    += amt
                profit_buckets[key] += profit

            ax.clear()
            if not rev_buckets:
                ax.text(0.5, 0.5, "No sales data yet", ha="center", va="center",
                        transform=ax.transAxes, fontsize=13, color="#7f8c8d")
                canvas_widget.draw()
                return

            labels = sorted(rev_buckets.keys())
            rev_vals    = [rev_buckets[l]    for l in labels]
            profit_vals = [profit_buckets[l] for l in labels]
            x     = np.arange(len(labels))
            width = 0.4

            bars_rev    = ax.bar(x - width/2, rev_vals,    width, label="Revenue", color=palette.primary,  edgecolor="white", linewidth=0.6)
            bars_profit = ax.bar(x + width/2, profit_vals, width, label="Profit",  color=palette.secondary, edgecolor="white", linewidth=0.6)

            ax.set_xticks(list(x))
            ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
            ax.set_ylabel("Amount (₱)", fontsize=9)
            ax.set_title(f"{period} Revenue vs Profit", fontsize=12, fontweight="bold", color=palette.text)
            ax.set_facecolor("#ffffff")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda v, _: f"₱{v:,.0f}")
            )
            ax.legend(loc="upper left", fontsize=8)

            max_val = max(max(rev_vals), 1)
            for bar, val in zip(bars_rev, rev_vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_val * 0.01,
                        f"₱{val:,.0f}", ha="center", va="bottom", fontsize=6, color=palette.text)
            for bar, val in zip(bars_profit, profit_vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max_val * 0.01,
                        f"₱{val:,.0f}", ha="center", va="bottom", fontsize=6, color=palette.secondary)

            fig.tight_layout()
            canvas_widget.draw()

        render_chart()

    # ── Right control panel — scrollable ─────────────────────────────────────
    right_outer = tk.Frame(main_content, bg=palette.bg, width=300)
    right_outer.pack(side="right", fill="y", padx=(40, 0))
    right_outer.pack_propagate(False)

    right_canvas = tk.Canvas(right_outer, bg=palette.bg, highlightthickness=0)
    right_scroll  = ttk.Scrollbar(right_outer, orient="vertical", command=right_canvas.yview)
    control_panel = tk.Frame(right_canvas, bg=palette.bg)

    control_panel.bind(
        "<Configure>",
        lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all"))
    )
    right_canvas.create_window((0, 0), window=control_panel, anchor="nw")
    right_canvas.configure(yscrollcommand=right_scroll.set)

    right_scroll.pack(side="right", fill="y")
    right_canvas.pack(side="left", fill="both", expand=True)

    def _on_mousewheel(event):
        right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    right_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # ── Edit Section ──────────────────────────────────────────────────────────
    edit_frame = tk.LabelFrame(control_panel, text=" Edit Selection ", bg="white",
                               padx=20, pady=20, font=BTN_FONT, relief="flat")
    edit_frame.pack(fill="x", pady=(0, 20))

    tk.Label(edit_frame, text="New Price (₱):", bg="white").pack(anchor="w")
    price_entry = tk.Entry(edit_frame, justify="center", font=("Segoe UI", 12),
                           bg=palette.bg, relief="flat")
    price_entry.pack(fill="x", pady=(5, 15), ipady=8)

    tk.Label(edit_frame, text="New Stock Level:", bg="white").pack(anchor="w")
    stock_entry = tk.Entry(edit_frame, justify="center", font=("Segoe UI", 12),
                           bg=palette.bg, relief="flat")
    stock_entry.pack(fill="x", pady=(5, 15), ipady=8)

    tk.Label(edit_frame, text="Category:", bg="white").pack(anchor="w")
    cat_var = tk.StringVar()
    cat_entry = tk.Entry(edit_frame, textvariable=cat_var, justify="center", font=("Segoe UI", 12),
                         bg=palette.bg, relief="flat")
    cat_entry.pack(fill="x", pady=(5, 15), ipady=8)
    
    tk.Label(edit_frame, text="New Cost (₱):", bg="white").pack(anchor="w")
    cost_entry = tk.Entry(edit_frame, justify="center", font=("Segoe UI", 12),
                           bg=palette.bg, relief="flat")
    cost_entry.pack(fill="x", pady=(5, 15), ipady=8)

    def save_edits():
        selected = tree.selection()
        if not selected:
            return messagebox.showwarning("Selection", "Select items first.")
        try:
            # 1. Get inputs from the entry boxes
            p = float(price_entry.get()) if price_entry.get() else None
            s = int(stock_entry.get())   if stock_entry.get() else None
            c = float(cost_entry.get())  if cost_entry.get() else None

            # Import the specific database functions
            cat_val = cat_var.get().strip() or None
            from db.products_db import save_price, set_stock, save_cost, save_category

            for item_id in selected:
                name = tree.item(item_id)['values'][0]
                key  = next((k for k in inventory if k.upper() == name), name)

                final_p = p if p is not None else inventory[key]['price']
                final_c = c if c is not None else inventory[key].get('cost', 0)
                profit  = final_p - final_c

                if final_p <= final_c:
                    messagebox.showerror("Invalid Pricing",
                        f"Error for {name}: Selling price (₱{final_p}) cannot be lower than cost (₱{final_c}).")
                    return

                if profit < 5:
                    confirm = messagebox.askyesno("Low Margin Warning",
                        f"Profit for '{name}' will only be ₱{profit:.2f}. Proceed anyway?")
                    if not confirm:
                        continue

                if p is not None:   save_price(key, p)
                if s is not None:   set_stock(key, s)
                if c is not None:   save_cost(key, c)
                if cat_val:         save_category(key, cat_val)

            # 4. Sync and Refresh UI
            save_to_disk()
            refresh_table()
            
            # Clear all entry fields
            price_entry.delete(0, tk.END)
            stock_entry.delete(0, tk.END)
            cost_entry.delete(0, tk.END)
            
            messagebox.showinfo("Success", "Inventory Updated successfully.")
            
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure Price, Cost, and Stock are valid numbers.")

    tk.Button(edit_frame, text="SAVE CHANGES", bg=palette.secondary, fg="white", font=BTN_FONT,
              relief="flat", pady=BTN_PAD_Y, cursor="hand2", command=save_edits).pack(fill="x")

    # ── Image Storage Section ─────────────────────────────────────────────────
    img_store = ImageStorage()

    img_frame = tk.LabelFrame(control_panel, text=" Product Image ", bg="white",
                              padx=20, pady=15, font=BTN_FONT, relief="flat")
    img_frame.pack(fill="x", pady=(0, 20))

    mode_row = tk.Frame(img_frame, bg="white")
    mode_row.pack(fill="x", pady=(0, 10))
    tk.Label(mode_row, text="Storage:", bg="white", font=("Segoe UI", 9)).pack(side="left")

    mode_var = tk.StringVar(value=img_store.mode)

    def _mode_label_color(mode):
        return palette.primary if mode == "cloudinary" else "#9b59b6"

    mode_indicator = tk.Label(mode_row, text=mode_var.get().upper(),
                              bg=_mode_label_color(mode_var.get()), fg="white",
                              font=("Segoe UI", 8, "bold"), padx=8, pady=3, relief="flat")
    mode_indicator.pack(side="left", padx=(6, 0))

    cloudinary_ready_lbl = tk.Label(
        mode_row,
        text="✓ creds set" if img_store.cloudinary_ready else "⚠ no creds",
        bg="white",
        fg=palette.secondary if img_store.cloudinary_ready else "#f39c12",
        font=("Segoe UI", 8)
    )
    cloudinary_ready_lbl.pack(side="left", padx=(6, 0))

    def _switch_mode(new_mode):
        try:
            img_store.set_mode(new_mode)
            mode_var.set(new_mode)
            mode_indicator.config(text=new_mode.upper(), bg=_mode_label_color(new_mode))
            cloudinary_ready_lbl.config(
                text="✓ creds set" if img_store.cloudinary_ready else "⚠ no creds",
                fg=palette.secondary if img_store.cloudinary_ready else "#f39c12"
            )
        except RuntimeError as e:
            messagebox.showerror("Storage Switch Failed", str(e))

    btn_toggle_row = tk.Frame(img_frame, bg="white")
    btn_toggle_row.pack(fill="x", pady=(0, 10))

    tk.Button(btn_toggle_row, text="☁  USE CLOUDINARY", bg=palette.primary, fg="white",
              relief="flat", font=("Segoe UI", 8, "bold"), padx=6, pady=5, cursor="hand2",
              command=lambda: _switch_mode("cloudinary")).pack(side="left", expand=True, fill="x", padx=(0, 4))

    tk.Button(btn_toggle_row, text="💾  USE LOCAL", bg="#9b59b6", fg="white",
              relief="flat", font=("Segoe UI", 8, "bold"), padx=6, pady=5, cursor="hand2",
              command=lambda: _switch_mode("local")).pack(side="left", expand=True, fill="x")

    upload_status_lbl = tk.Label(img_frame, text="Select one item, then upload.",
                                 bg="white", font=("Segoe UI", 8), fg="#7f8c8d",
                                 wraplength=230, justify="left")
    upload_status_lbl.pack(anchor="w", pady=(0, 6))

    def _upload_image():
        selected = tree.selection()
        if len(selected) != 1:
            messagebox.showwarning("Selection", "Select exactly ONE item to upload an image for.")
            return
        raw_name = tree.item(selected[0])['values'][0]
        item_key = next((k for k in inventory if k.upper() == raw_name), raw_name)
        file_path = filedialog.askopenfilename(
            title="Choose product image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.gif"), ("All files", "*.*")]
        )
        if not file_path:
            return
        upload_status_lbl.config(text="⏳ Uploading…", fg=palette.primary)
        window.update_idletasks()

        def _do_upload():
            try:
                url   = img_store.upload(file_path, public_id=item_key)
                update_image_url(item_key, url)
                short = os.path.basename(url) if img_store.mode == "local" else url.split("/")[-1]
                window.after(0, lambda: upload_status_lbl.config(text=f"Saved: {short}", fg=palette.secondary))
            except Exception as e:
                window.after(0, lambda e=e: upload_status_lbl.config(text=f"Error: {e}", fg=palette.danger))

        threading.Thread(target=_do_upload, daemon=True).start()

    tk.Button(img_frame, text="📁  UPLOAD IMAGE", bg=palette.text, fg="white", relief="flat",
              font=BTN_FONT, pady=8, cursor="hand2", command=_upload_image).pack(fill="x")

    def _remove_image():
        selected = tree.selection()
        if len(selected) != 1:
            messagebox.showwarning("Selection", "Select exactly ONE item to remove its image.")
            return
        raw_name = tree.item(selected[0])['values'][0]
        item_key = next((k for k in inventory if k.upper() == raw_name), raw_name)
        if not messagebox.askyesno("Remove Image", f"Remove image for {item_key}?"):
            return
        try:
            img_store.delete(item_key)
            update_image_url(item_key, "")
            upload_status_lbl.config(text="Image removed.", fg="#7f8c8d")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    tk.Button(img_frame, text="🗑  REMOVE IMAGE", bg=palette.danger, fg="white", relief="flat",
              font=("Segoe UI", 9, "bold"), pady=6, cursor="hand2",
              command=_remove_image).pack(fill="x", pady=(6, 0))

    # ── Inventory Tools ───────────────────────────────────────────────────────
    maint_frame = tk.LabelFrame(control_panel, text=" Inventory Tools ", bg="white",
                                padx=20, pady=20, font=BTN_FONT, relief="flat")
    maint_frame.pack(fill="x", pady=(0, 20))

    tk.Button(maint_frame, text="SHOW ALL ITEMS", bg=palette.text, fg="white",
              font=("Segoe UI", 9, "bold"), relief="flat", pady=8,
              command=lambda: refresh_table(False)).pack(fill="x", pady=(0, 5))

    tk.Button(maint_frame, text="SHOW LOW STOCK", bg="#f39c12", fg="white",
              font=("Segoe UI", 9, "bold"), relief="flat", pady=8,
              command=lambda: refresh_table(True)).pack(fill="x", pady=(0, 15))

    def restock_all():
        if messagebox.askyesno("Restock All", "Add 100 units to all items?"):
            from db.products_db import restock_all as db_restock
            db_restock(100)
            save_to_disk()
            refresh_table()

    tk.Button(maint_frame, text="RESTOCK ALL (100)", bg="#9b59b6", fg="white", font=BTN_FONT,
              relief="flat", pady=BTN_PAD_Y, cursor="hand2", command=restock_all).pack(fill="x")

    # ── Add / Delete Product ─────────────────────────────────────────────────
    product_frame = tk.LabelFrame(control_panel, text=" Add / Delete Product ", bg="white",
                                  padx=20, pady=20, font=BTN_FONT, relief="flat")
    product_frame.pack(fill="x", pady=(0, 20))

    tk.Label(product_frame, text="Product Name:", bg="white").pack(anchor="w")
    new_name_entry = tk.Entry(product_frame, justify="center", font=("Segoe UI", 11),
                              bg=palette.bg, relief="flat")
    new_name_entry.pack(fill="x", pady=(4, 12), ipady=7)

    tk.Label(product_frame, text="Price (₱):", bg="white").pack(anchor="w")
    new_price_entry = tk.Entry(product_frame, justify="center", font=("Segoe UI", 11),
                               bg=palette.bg, relief="flat")
    new_price_entry.pack(fill="x", pady=(4, 12), ipady=7)

    tk.Label(product_frame, text="Initial Stock:", bg="white").pack(anchor="w")
    new_stock_entry = tk.Entry(product_frame, justify="center", font=("Segoe UI", 11),
                               bg=palette.bg, relief="flat")
    new_stock_entry.insert(0, "50")
    new_stock_entry.pack(fill="x", pady=(4, 12), ipady=7)

    tk.Label(product_frame, text="Category:", bg="white").pack(anchor="w")
    new_cat_entry = tk.Entry(product_frame, justify="center", font=("Segoe UI", 11),
                             bg=palette.bg, relief="flat")
    new_cat_entry.insert(0, "All")
    new_cat_entry.pack(fill="x", pady=(4, 12), ipady=7)

    tk.Label(product_frame, text="Unit Cost (₱):", bg="white").pack(anchor="w")
    new_cost_entry = tk.Entry(product_frame, justify="center", font=("Segoe UI", 11), bg=palette.bg, relief="flat")
    new_cost_entry.pack(fill="x", pady=(4, 12), ipady=7)

    def add_product():
        name = new_name_entry.get().strip()
        price_str = new_price_entry.get().strip()
        stock_str = new_stock_entry.get().strip()
        cost_str = new_cost_entry.get().strip()

        if not (name and price_str and stock_str and cost_str):
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        try:
            price = float(price_str)
            cost = float(cost_str)
            stock = int(stock_str)
            profit = price - cost

            # 1. STOP: Block if selling at a loss
            if price <= cost:
                messagebox.showerror("Pricing Error", 
                    f"Invalid Price: You cannot sell '{name}' for less than it costs (₱{cost}).\n"
                    f"Current Profit: ₱{profit}")
                return

            # 2. WARN: Alert if profit is less than 5
            if profit < 5:
                confirm = messagebox.askyesno("Low Profit Warning", 
                    f"The profit for '{name}' is only ₱{profit:.2f}.\n"
                    "This is below the ₱5.00 threshold. Do you wish to continue?")
                if not confirm:
                    return

            # 3. PROCEED: Database and Disk Sync
            from db.products_db import add_product as db_add
            ok, msg = db_add(name, price, stock, cost)
            
            if ok:
                save_to_disk() # Local Repo Sync
                refresh_table()
                new_name_entry.delete(0, tk.END)
                new_price_entry.delete(0, tk.END)
                new_stock_entry.delete(0, tk.END)
                new_stock_entry.insert(0, "50")
                new_cost_entry.delete(0, tk.END)
                messagebox.showinfo("Success", "Product added and synced successfully.")
            else:
                messagebox.showerror("Error", msg)

        except ValueError:
            messagebox.showerror("Format Error", "Please ensure Price, Cost, and Stock are valid numbers.")
            
    def delete_selected():
        selected = tree.selection()
        if not selected:
            return messagebox.showwarning("Selection", "Select at least one item to delete.")
        names = [tree.item(i)['values'][0] for i in selected]
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete {len(names)} item(s)?\n" + "\n".join(names)):
            return
        from db.products_db import delete_product as db_del
        for raw_name in names:
            key = next((k for k in inventory if k.upper() == raw_name), raw_name)
            db_del(key)
        save_to_disk()
        refresh_table()
        messagebox.showinfo("Deleted", f"{len(names)} item(s) removed.")

    tk.Button(product_frame, text="➕  ADD PRODUCT", bg=palette.secondary, fg="white",
              font=BTN_FONT, relief="flat", pady=BTN_PAD_Y, cursor="hand2",
              command=add_product).pack(fill="x", pady=(0, 8))

    tk.Button(product_frame, text="🗑  DELETE SELECTED", bg=palette.danger, fg="white",
              font=BTN_FONT, relief="flat", pady=BTN_PAD_Y, cursor="hand2",
              command=delete_selected).pack(fill="x")


    # ── Reports & Logs ────────────────────────────────────────────────────────
    reports_frame = tk.LabelFrame(control_panel, text=" Reports & Logs ", bg="white",
                                  padx=20, pady=20, font=BTN_FONT, relief="flat")
    reports_frame.pack(fill="x", pady=(0, 20))

    tk.Button(reports_frame, text="📋  VIEW SALES HISTORY", bg=palette.primary, fg="white",
              font=BTN_FONT, relief="flat", pady=BTN_PAD_Y, cursor="hand2",
              command=open_history_log).pack(fill="x", pady=(0, 8))

    tk.Button(reports_frame, text="📊  SALES ANALYTICS", bg=palette.secondary, fg="white",
              font=BTN_FONT, relief="flat", pady=BTN_PAD_Y, cursor="hand2",
              command=open_sales_chart).pack(fill="x")

    # ── Initial Load ──────────────────────────────────────────────────────────
    low_stock_found = refresh_table()
    if low_stock_found > 0:
        messagebox.showwarning("Inventory Alert",
                               f"There are {low_stock_found} items with low stock (<10)!")
