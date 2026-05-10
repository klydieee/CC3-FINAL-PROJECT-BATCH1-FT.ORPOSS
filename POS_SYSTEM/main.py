import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import datetime

from data.inventory import inventory
from utils.helper import peso
from utils.receipt_generator import generate_receipt_file
from ui.receipt_popup import show_receipt_popup

# --- STYLING CONSTANTS ---
COLOR_BG = "#1a3c40"  # Modern Teal
COLOR_WIN95 = "#d0d0d0" # Retro Grey

class MainSystem(ctk.CTk):
    def __init__(self, user_role=None):
        super().__init__()
        self.user_role = user_role
        self.title("ULTRA-POS 95: FAST FOOD EDITION")
        self.geometry("1200x700")
        self.configure(fg_color=COLOR_BG)

        # State management from friend's logic
        self.cart = []
        self.total_state = 0.0
        self.menu_buttons = {}

        # 1. Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 2. Sidebar (Win95 Aesthetic)
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLOR_WIN95)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text=f"USER: {self.user_role}", 
                     font=("Courier", 12, "italic"), text_color="#1a3c40").pack(side="bottom", pady=10)

        # 3. Add an "Inventory Manager" button only for Admins
        if self.user_role == "Admin":
            self.btn_admin = ctk.CTkButton(self.sidebar, text=" [F2] INVENTORY", 
                                           fg_color="#800000", corner_radius=0,
                                           command=self.show_inventory_settings)
            self.btn_admin.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.sidebar, text="POS TERMINAL", font=("Courier", 20, "bold"), text_color="black").pack(pady=20)

        # Using your itch.io assets idea for the sidebar
        self.btn_pos = ctk.CTkButton(self.sidebar, text=" [F1] CASHIER", font=("Courier", 14), 
                                     fg_color="transparent", text_color="black", hover_color="#bdbdbd",
                                     command=self.show_pos_screen)
        self.btn_pos.pack(fill="x", padx=10, pady=5)

        # 3. Main View Container
        self.main_view = tk.Frame(self, bg="#e6e6e6", bd=2, relief="sunken")
        self.main_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.show_pos_screen()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to exit the system?"):
            self.destroy()
            import sys
            sys.exit()

    def clear_view(self):
        for widget in self.main_view.winfo_children(): widget.destroy()
        
    def remove_item_from_cart(self):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            # Get item name from the cart list
            item_name, price = self.cart.pop(index)
            
            # Restore stock and update state
            inventory[item_name]["stock"] += 1
            self.total_state -= price
            
            # Refresh everything
            self.update_cart_display()
            self.recalculate_grid() # Refresh numerical stock on boxes

    def show_pos_screen(self):
        self.clear_view()
        
        # Right Panel: Cart/Receipt (Modernized)
        cart_panel = tk.Frame(self.main_view, bg="white", width=350, bd=2, relief="sunken")
        cart_panel.pack(side="right", fill="y", padx=10, pady=10)
        cart_panel.pack_propagate(False)
        ctk.CTkButton(cart_panel, text="VOID SELECTED", fg_color="#e74c3c", 
               command=self.remove_item_from_cart).pack(pady=5, padx=20, fill="x")

        self.listbox = tk.Listbox(cart_panel, font=("Courier", 10), bd=0, bg="white")
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.listbox.bind('<Double-1>', lambda e: self.remove_item_from_cart())

        self.lbl_total = tk.Label(cart_panel, text="TOTAL: ₱0.00", font=("Arial", 16, "bold"), bg="white", fg="#27ae60")
        self.lbl_total.pack(pady=5)

        self.cash_entry = ctk.CTkEntry(cart_panel, placeholder_text="Enter Cash", corner_radius=0)
        self.cash_entry.pack(pady=5, padx=20)

        ctk.CTkButton(cart_panel, text="PROCESS TRANSACTION", fg_color="#27ae60", corner_radius=0, 
                       command=self.checkout_logic).pack(pady=10, padx=20, fill="x")

        # We use a standard Frame inside the ScrollableFrame to hold the items
        self.menu_scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="#e6e6e6", corner_radius=0)
        self.menu_scroll.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # This inner frame is what we will grid the items into
        self.items_area = tk.Frame(self.menu_scroll, bg="#e6e6e6")
        self.items_area.pack(fill="both", expand=True)

        # Bind the resize event to our recalculation function
        self.items_area.bind("<Configure>", lambda e: self.recalculate_grid())
        
        # Initial draw
        self.recalculate_grid()

    def recalculate_grid(self):
        # Clear current grid positions (but don't destroy widgets)
        for slave in self.items_area.grid_slaves():
            slave.grid_forget()

        # Calculate how many columns can fit
        # We assume each box is ~220px wide (200px + padding)
        width = self.items_area.winfo_width()
        num_columns = max(1, width // 220) 

        # Re-grid the items
        r, c = 0, 0
        for name in inventory:
            # We create the box if it doesn't exist, otherwise we just re-grid it
            box = self.create_item_box(self.items_area, name) 
            box.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            
            c += 1
            if c >= num_columns:
                c = 0
                r += 1
        
        # Make the columns expand to fill the leftover "span"
        for i in range(num_columns):
            self.items_area.grid_columnconfigure(i, weight=1)

    def create_item_box(self, parent, name):
        # 1. Initialize the box
        box = ctk.CTkFrame(parent, width=200, height=240, corner_radius=0, 
                           border_width=2, border_color="#808080", fg_color=COLOR_WIN95)
        box.pack_propagate(False) 

        # 2. Define the Image Label (even if empty)
        try:
            from PIL import Image # Ensure this is at the top of main.py too
            img_path = f"assets/items/{name.lower()}.png"
            img_data = ctk.CTkImage(Image.open(img_path), size=(100, 100))
            img_label = ctk.CTkLabel(box, image=img_data, text="")
        except:
            img_label = ctk.CTkLabel(box, text="[ NO IMAGE ]", font=("Courier", 12))
        
        img_label.pack(pady=(10, 0))

        # 3. Define Name and Price Labels
        lbl_name = ctk.CTkLabel(box, text=name.upper(), font=("Courier", 14, "bold"), text_color="black")
        lbl_name.pack()

        # Numerical Stock Display
        current_stock = inventory[name]['stock']
        lbl_stock = ctk.CTkLabel(box, text=f"QTY: {current_stock}", 
                                 font=("Courier", 12), 
                                 text_color="red" if current_stock < 5 else "green")
        lbl_stock.pack()

        lbl_price = ctk.CTkLabel(box, text=peso(inventory[name]['price']), font=("Courier", 14), text_color="#1a3c40")
        lbl_price.pack(pady=(0, 5))

        # 4. NOW define the elements list (Everything is guaranteed to exist now)
        elements = [box, img_label, lbl_name, lbl_stock, lbl_price]
        
        for widget in elements:
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda e, n=name: self.add_item_logic(n))
            # Hover effect for the whole box
            widget.bind("<Enter>", lambda e: box.configure(fg_color="#bdbdbd"))
            widget.bind("<Leave>", lambda e: box.configure(fg_color=COLOR_WIN95))

        return box

    # --- INTEGRATED LOGIC FROM YOUR FRIEND ---
    def add_item_logic(self, name):
        if inventory[name]["stock"] <= 0:
            messagebox.showwarning("Out of Stock", f"{name} is unavailable")
            return
        
        self.cart.append((name, inventory[name]["price"]))
        self.total_state += inventory[name]["price"]
        inventory[name]["stock"] -= 1
        
        self.update_cart_display()
        self.refresh_menu_display()
        
        self.save_inventory_to_file()
        
        self.update_cart_display()
        self.refresh_menu_display()
        
    def update_price(self, name, var):
        try:
            new_price = float(var.get())
            inventory[name]['price'] = new_price # Update memory
            
            # Save to file
            self.save_inventory_to_file()
            
            messagebox.showinfo("Success", f"Updated {name} price to {peso(new_price)}")
        except ValueError:
            messagebox.showerror("Error", "Invalid price amount")
            
    def save_inventory_to_file(self):
        import os
        try:
            # Get the directory where main.py is located
            base_path = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_path, "data")
            file_path = os.path.join(data_dir, "inventory.py")

            # 1. Ensure the 'data' directory actually exists
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # 2. Write the file using the absolute path
            with open(file_path, "w") as f:
                f.write(f"inventory = {repr(inventory)}")
                
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save data: {e}")

    def update_cart_display(self):
        self.listbox.delete(0, tk.END)
        for item, price in self.cart:
            self.listbox.insert(tk.END, f" {item:<15} {peso(price):>10}")
        self.lbl_total.config(text=f"TOTAL: {peso(self.total_state)}")

    def refresh_menu_display(self):
        for name, btn in self.menu_buttons.items():
            stock = inventory[name]['stock']
            btn.config(
                text=f"{name}\n{peso(inventory[name]['price'])}\nStock: {stock}",
                state="normal" if stock > 0 else "disabled",
                bg="#ffffff" if stock > 0 else "#dfe6e9"
            )

    def checkout_logic(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add items first!")
            return

        try:
            cash = float(self.cash_entry.get())
        except:
            messagebox.showerror("Error", "Invalid Cash Amount")
            return

        if cash < self.total_state:
            messagebox.showerror("Error", "Insufficient Cash")
            return

        # Prepare data for preview
        change = cash - self.total_state
        invoice_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        summary = {}
        for item, price in self.cart:
            if item in summary: summary[item]["qty"] += 1
            else: summary[item] = {"qty": 1, "price": price}

        # Format the text for the preview
        receipt_text = f"--- TRANSACTION PREVIEW ---\nINVOICE: {invoice_no}\n" + "-"*30 + "\n"
        for item, data in summary.items():
            receipt_text += f"{item:<15} x{data['qty']} {peso(data['qty']*data['price'])}\n"
        receipt_text += "-"*30 + f"\nTOTAL: {peso(self.total_state)}\nCASH: {peso(cash)}\nCHANGE: {peso(change)}"

        # ASK FOR CONFIRMATION
        if messagebox.askyesno("Confirm Purchase", f"{receipt_text}\n\nProceed with payment?"):
            self.finalize_transaction(cash, change, invoice_no, summary)
        
        if messagebox.askyesno("Confirm Purchase", f"{receipt_text}\n\nProceed with payment?"):
            
            generate_receipt_file(cash, change, invoice_no, self.total_state, summary)
            show_receipt_popup(self, receipt_text)
            
            # 1. Generate the physical file
            generate_receipt_file(cash, change, invoice_no, self.total_state, summary)
            
            # 2. Show the final success popup
            show_receipt_popup(self, "TRANSACTION COMPLETE")

            # 3. Only now do we clear the cart and reset variables
            self.cart = []
            self.total_state = 0.0
            self.cash_entry.delete(0, 'end')
            
            # 4. Refresh the UI
            self.update_cart_display()
            self.recalculate_grid() 
            
            # 5. Save the final inventory state to data/inventory.py
            self.save_inventory_to_file()
        else:
            # If they click NO, we do nothing. 
            # The cart stays full and the cash entry stays filled.
            pass

        # Reset session
        self.cart = []
        self.total_state = 0.0
        self.cash_entry.delete(0, 'end')
        self.update_cart_display()
        
    def finalize_transaction(self, cash, change, invoice_no, summary):
        # 1. Generate the actual physical file
        generate_receipt_file(cash, change, invoice_no, self.total_state, summary)
        
        # 2. Lower stock and PERSIST to data/inventory.py
        # Stock was already lowered in add_item_logic, so we just ensure it's saved
        self.save_inventory_to_file()

        # 3. Show the final success popup
        show_receipt_popup(self, "TRANSACTION COMPLETE\nReceipt has been printed.")

        # 4. Reset the UI session
        self.cart = []
        self.total_state = 0.0
        self.cash_entry.delete(0, 'end')
        self.update_cart_display()
        # This forces the boxes to update their numerical stock display
        self.recalculate_grid()
        
    def show_inventory_settings(self):
        self.clear_view()
        ctk.CTkLabel(self.main_view, text="INVENTORY & STOCK CONTROL", font=("Courier", 24, "bold")).pack(pady=20)
        
        scroll = ctk.CTkScrollableFrame(self.main_view, fg_color="white")
        scroll.pack(pady=10, padx=20, fill="both", expand=True)

        for name, details in inventory.items():
            row = ctk.CTkFrame(scroll, fg_color="#f0f0f0")
            row.pack(fill="x", pady=5, padx=10)
            
            ctk.CTkLabel(row, text=f"{name.upper():<15}", text_color="black", font=("Courier", 14)).pack(side="left", padx=10)
            
            # Current Stock Label
            ctk.CTkLabel(row, text=f"In Stock: {details['stock']}", width=100).pack(side="left", padx=10)

            # Price Edit
            price_var = tk.StringVar(value=str(details['price']))
            ctk.CTkEntry(row, textvariable=price_var, width=80).pack(side="right", padx=5)
            
            # Add Stock Entry
            stock_add_var = tk.StringVar(value="0")
            ctk.CTkEntry(row, textvariable=stock_add_var, width=50).pack(side="right", padx=5)
            ctk.CTkLabel(row, text="+ Add Stock:").pack(side="right")

            # Save Button
            save_btn = ctk.CTkButton(row, text="UPDATE", width=100, fg_color="#27ae60",
                                    command=lambda n=name, p=price_var, s=stock_add_var: self.update_inventory(n, p, s))
            save_btn.pack(side="right", padx=10)

    def update_inventory(self, name, p_var, s_var):
        try:
            # Update Price and Stock
            inventory[name]['price'] = float(p_var.get())
            inventory[name]['stock'] += int(s_var.get())
            
            # PERSISTENCE: Save to file
            self.save_inventory_to_file()
            
            messagebox.showinfo("Success", f"Updated {name} successfully!")
            self.show_inventory_settings() # Refresh view
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def update_price(self, name, var):
        try:
            new_price = float(var.get())
            inventory[name]['price'] = new_price
            messagebox.showinfo("Success", f"Updated {name} price to {peso(new_price)}")
        except ValueError:
            messagebox.showerror("Error", "Invalid price amount")

if __name__ == "__main__":
    from ui.login import start_login
    start_login()
    app = MainSystem()
    app.mainloop()