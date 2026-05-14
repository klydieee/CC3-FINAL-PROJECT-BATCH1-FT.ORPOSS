# ORPOSS Ordering & Fast Food POS System

**Developed by BSIT 1-5 BATCH #1**

<img alt="Operational Flowchart" src="docs/ORPOSS%20SYSTEMS%20OPERATIONAL%20DETAILED%20ANALYSIS.jpg" width="100%"/>

A modular, desktop-based Point of Sale (POS) & Ordering System (OS) built with Python and Tkinter. This project demonstrates clean UI/UX design, inventory management, and modular software architecture for academic and professional applications.

## 🚀 Features

**Client-Side (Kiosk / User Device)**
* **Ordering:** Browse menus by Order types (Dine-in/Take-out), and apply customization filters to items.
* **Payment Processing:** Integrated payment gateway calls with real-time payment status displays, failure logging, and retry options.
* **Responsive Design:** Modular frames for easy screen switching and intuitive UI for reviewing and submitting orders.

**Admin-Side (Kitchen Operations and Admin Panel)**
* **Kitchen Dashboard & API:** Centralized dashboard for backend order processing, tracking fulfillment decisions, and updating order statuses (Ready, Completed).
* **Advanced Inventory Management:** Real-time stock checks, automated inventory reservation upon payment, and a dedicated "Out-of-Stock" workflow that syncs back to the client side.
* **Fulfillment Operations:** Automatic generation and printing of fulfillment packing lists.
* **Sales & Reporting Engine:** Automatically compiles sales data (Daily, Weekly, Monthly, and Hourly logs) and generates detailed financial reports.
* **Secure Login:** Role-based access control for administrative and backend features.

**Database-Side (Centralized Storage Server)**
* **Data Management:** Dedicated read/write tables for Order Master Data, Inventory Data, Payment Logs, Fulfillment Status History, and Payment Logic.
* **Archiving:** Automatic compilation of completed records into a secure Sales Archive(Receipt).

## 🛠️ Installation

1. Ensure you have Python 3.12+ installed.
2. Clone the repository:
   ```bash
   git clone <your-repository-link>