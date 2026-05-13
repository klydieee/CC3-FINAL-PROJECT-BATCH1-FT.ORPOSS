# ─── Global Color Palette ───────────────────────────────────────────────────
class palette:
    bg         = "#f8f9fa"  # Light Grey/White
    text       = "#2c3e50"  # Dark Blue/Grey
    primary    = "#e67e22"  # Orange
    secondary  = "#2ecc71"  # Green
    win95      = "#d0d0d0"  # Classic Grey
    teal       = "#1a3c40"  # Dark Teal
    danger     = "#e74c3c"  # Red

    @classmethod
    def to_dict(cls):
        """Returns all colors as a dictionary if needed for iteration."""
        return {
            "bg": cls.bg,
            "text": cls.text,
            "primary": cls.primary,
            "secondary": cls.secondary,
            "win95": cls.win95,
            "teal": cls.teal,
            "danger": cls.danger
        }