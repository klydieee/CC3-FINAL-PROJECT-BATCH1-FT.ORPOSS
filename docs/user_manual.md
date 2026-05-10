# User Manual

## Getting Started
1. Launch `main.py`.
2. Enter the Admin credentials (Default: admin/123).

## Processing an Order
1. Click on the menu items in the grid. 
2. If an item is out of stock, the button will automatically disable.
3. To remove everything, click **Clear Order**.
4. Enter the cash amount provided by the customer.
5. Click **Process Checkout** to view the change and generate a receipt.

## Troubleshooting
- **Receipt not saving:** Ensure you have write permissions in the `pos_system/receipts/` folder.
- **Stock not updating:** Check if `inventory.json` is being updated in the data directory.