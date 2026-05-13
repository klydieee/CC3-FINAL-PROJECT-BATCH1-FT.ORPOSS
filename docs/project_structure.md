# Project Structure

This document provides a map of the repository's layout and the purpose of each component within the **Fast Food POS System**.

## File Tree

```text
/Project Root
├── .git/                           # Hidden: Version control history
├── .gitignore                      # Configuration: Prevents tracking of temporary/junk files
├── LICENSE                         # Legal: MIT License (Permissions)
├── README.md                       # Documentation: Project overview & instructions
├── requirements.txt                # Dependency: Confirms zero-dependency build
├── docs/                           # Directory: Project Documentation
│   ├── system_architecture.md      # Technical breakdown of modules
│   ├── project_structure.md        # <= You are here right now 
│   ├── user_manual.md              # Step-by-step instructions for the cashier
│   └── technical_specs.md          # Environmental and system requirements
└── ORPOSS/                         # Directory: Main Source Code Package
    ├── main.py                     # Entry Point: Run this file to start the app
    ├── data/                       # Sub-package: Data persistence management
    │   └── inventory.py            # Inventory dictionary and logic
    ├── ui/                         # Sub-package: GUI components
    │   ├── login.py                # Authentication screen logic
    │   ├── dashboard.py            # Main POS interface and cart logic
    │   ├── kitchen_panel.py        # Kitchen area procedural system
    │   ├── user_queue.py           # User ordering guide for waiting and dining area
    │   ├── receipt_popup.py        # Modal window for transaction display
    │   ├── admin_panel.py          # Full access to Sales and Inventory
    │   ├── order_review.py         # Sub window to review order before payment
    │   └── order_type.py           # Dining options
    ├── utils/                      # Sub-package: Helper functions
    │   ├── helper.py               # Formatting tools (e.g., Currency/Peso)
    │   └── receipt_generator.py    # File I/O for .txt receipts
    └── receipts/                   # Output: Automatically saved transaction files