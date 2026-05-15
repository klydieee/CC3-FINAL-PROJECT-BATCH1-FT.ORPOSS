def clear_main_window(window):
    for widget in window.winfo_children():
        # should stay visible while the main screen is rebuilt.
        if getattr(widget, "_keep_on_screen_change", False):
            continue
        # All normal widgets belong to the current screen, so destroying them
        # gives the next screen a clean parent window to render into.
        widget.destroy()