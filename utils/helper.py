def peso(value):
    try:
        return f"₱{float(value):,.2f}"
    except (ValueError, TypeError):
        return "₱0.00"
