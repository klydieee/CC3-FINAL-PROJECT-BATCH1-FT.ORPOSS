class palette:
    bg         = "#f0e6d7"  # Tan
    text       = "#8a0000"  # Dark Blue/Grey /maroon
    primary    = "#ff7a00"  # Orange
    secondary  = "#633209"  # Brown
    win95      = "#d0d0d0"  # Classic Grey
    teal       = "#cd1818"  # Dark Teal /red
    danger     = "#e67e22"  # Red

    @classmethod
    def to_dict(cls):
        # Returns
        return {
            "bg": cls.bg,
            "text": cls.text,
            "primary": cls.primary,
            "secondary": cls.secondary,
            "win95": cls.win95,
            "teal": cls.teal,
            "danger": cls.danger
        }