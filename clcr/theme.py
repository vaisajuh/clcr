"""Dark ttk theme for the control center."""

import tkinter as tk
from tkinter import font, ttk

BG = "#1b1d23"
SURFACE = "#23262e"
FIELD = "#2d313b"
BORDER = "#383c48"
FG = "#e7e9ee"
MUTED = "#9aa1ad"
ACCENT = "#5b8cff"
ACCENT_HOVER = "#7aa2ff"
OK = "#3ecf8e"
ERROR = "#ff6b6b"
PENDING = "#f5b84a"

STATUS_COLORS = {"ok": OK, "error": ERROR, "pending": PENDING, "off": MUTED}


def apply(root: tk.Tk):
    base = font.nametofont("TkDefaultFont")
    base.configure(size=10)
    family = base.actual("family")
    title_font = font.Font(root, family=family, size=15, weight="bold")
    heading_font = font.Font(root, family=family, size=10, weight="bold")
    small_font = font.Font(root, family=family, size=9)

    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.background", FIELD)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "white")
    root.option_add("*TCombobox*Listbox.borderWidth", 0)

    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=FG, fieldbackground=FIELD,
                bordercolor=BORDER, lightcolor=BG, darkcolor=BG, troughcolor=FIELD,
                focuscolor=BG, selectbackground=ACCENT, selectforeground="white",
                insertcolor=FG, arrowcolor=FG)

    s.configure("TFrame", background=BG)
    s.configure("Card.TFrame", background=SURFACE)
    s.configure("TLabel", background=BG, foreground=FG)
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("Small.TLabel", foreground=MUTED, font=small_font)
    s.configure("Title.TLabel", font=title_font)
    s.configure("Heading.TLabel", font=heading_font)
    s.configure("Card.TLabel", background=SURFACE)
    s.configure("CardMuted.TLabel", background=SURFACE, foreground=MUTED)
    s.configure("CardTitle.TLabel", background=SURFACE, font=heading_font)
    for name, color in STATUS_COLORS.items():
        s.configure(f"{name.title()}.TLabel", foreground=color)
        s.configure(f"Card{name.title()}.TLabel", background=SURFACE, foreground=color)
    s.configure("Statusbar.TLabel", background=SURFACE, foreground=MUTED, padding=(12, 5))

    s.configure("TLabelframe", background=BG, bordercolor=BORDER, relief="solid", borderwidth=1)
    s.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=heading_font)

    s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(12, 8, 12, 0))
    s.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED, padding=(18, 8),
                borderwidth=0, lightcolor=SURFACE, bordercolor=BG)
    s.map("TNotebook.Tab", background=[("selected", FIELD), ("active", FIELD)],
          foreground=[("selected", FG)])

    s.configure("TButton", background=FIELD, foreground=FG, padding=(12, 6),
                borderwidth=0, lightcolor=FIELD, darkcolor=FIELD)
    s.map("TButton", background=[("disabled", SURFACE), ("active", BORDER)],
          foreground=[("disabled", MUTED)])
    s.configure("Accent.TButton", background=ACCENT, foreground="white",
                lightcolor=ACCENT, darkcolor=ACCENT)
    s.map("Accent.TButton", background=[("disabled", SURFACE), ("active", ACCENT_HOVER)])

    s.configure("TCombobox", fieldbackground=FIELD, background=FIELD, foreground=FG,
                bordercolor=BORDER, lightcolor=FIELD, darkcolor=FIELD, padding=4)
    s.map("TCombobox",
          fieldbackground=[("disabled", SURFACE), ("readonly", FIELD)],
          foreground=[("disabled", MUTED)],
          selectbackground=[("readonly", FIELD)], selectforeground=[("readonly", FG)])

    s.configure("TSpinbox", fieldbackground=FIELD, background=FIELD, foreground=FG,
                bordercolor=BORDER, lightcolor=FIELD, darkcolor=FIELD, padding=3)

    s.configure("Horizontal.TScale", background=ACCENT, troughcolor=FIELD,
                bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT)
    s.map("Horizontal.TScale", background=[("disabled", BORDER), ("active", ACCENT_HOVER)])

    for widget in ("TCheckbutton", "TRadiobutton"):
        s.configure(widget, background=BG, foreground=FG, indicatorbackground=FIELD,
                    indicatorforeground="white", upperbordercolor=BORDER,
                    lowerbordercolor=BORDER)
        s.map(widget, indicatorbackground=[("selected", ACCENT), ("disabled", SURFACE)],
              foreground=[("disabled", MUTED)], background=[("active", BG)])
