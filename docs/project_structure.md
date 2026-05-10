# Project Structure

This document provides a map of the repository's layout and the purpose of each component within the **Fast Food POS System**.

## File Tree

```text
/ (Project Root)
├── .git/                           # Hidden: Version control history
├── .gitignore                      # Configuration: Prevents tracking of temporary/junk files
├── LICENSE                         # Legal: MIT License (Permissions)
├── README.md                       # Documentation: Project overview & instructions
├── requirements.txt                # Dependency: Confirms zero-dependency build
├── docs/                           # Directory: Project Documentation
│   ├── system_architecture.md      # Technical breakdown of modules
│   ├── user_manual.md              # Step-by-step instructions for the cashier
│   └── technical_specs.md          # Environmental and system requirements
└── pos_system/                     # Directory: Main Source Code Package
    ├── main.py                     # Entry Point: Run this file to start the app
    ├── data/                       # Sub-package: Data persistence management
    │   └── inventory.py            # Inventory dictionary and logic
    ├── ui/                         # Sub-package: GUI components
    │   ├── login.py                # Authentication screen logic
    │   ├── dashboard.py            # Main POS interface and cart logic
    │   └── receipt_popup.py        # Modal window for transaction display
    ├── utils/                      # Sub-package: Helper functions
    │   ├── helper.py               # Formatting tools (e.g., Currency/Peso)
    │   └── receipt_generator.py    # File I/O for .txt receipts
    └── receipts/                   # Output: Automatically saved transaction files