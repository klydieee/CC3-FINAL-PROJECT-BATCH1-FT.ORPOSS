import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import sys
import os

from utils.palette import palette

def start_kitchen_panel(window):
    for w in window.winfo_children():
        w.destroy()

    if isinstance(window, ctk.Ctk):
        window.configure(palette.bg)
    else:
        window.configure(palette.bg)

    header = tk.Frame(window, bg=palette.bg, height=70)
    header.pack(fill="x")
