# System Architecture

## Overview
The system follows a modular structure where the UI is separated from the data logic.

## Components
1. **Main Entry (`main.py`)**: The bootstrapper that starts the application.
2. **Login Module (`ui/login.py`)**: Handles user authentication and transitions to the dashboard.
3. **Dashboard Module (`ui/dashboard.py`)**: The main POS interface and cart logic.
4. **Data Layer (`data/inventory.py`)**: Manages the JSON-based product database.
5. **Utils (`utils/`)**: Helper functions for currency formatting and receipt file I/O.

## Data Flow
User Input -> Validation -> State Update (Cart/Stock) -> Receipt Generation.