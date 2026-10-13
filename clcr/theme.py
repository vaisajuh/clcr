"""Dark ttk theme for the control center."""

import base64
import math
import struct
import tkinter as tk
import zlib
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
    # Tk deletes a font when its Python object is garbage collected, so keep them alive.
    root._theme_fonts = (title_font, heading_font, small_font)

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
    # A filled section with its heading inside; see restyle_cards() for its contents.
    s.configure("Card.TLabelframe", background=SURFACE, borderwidth=0, relief="flat",
                labelmargins=(16, 12, 16, 0))
    s.configure("Card.TLabelframe.Label", background=SURFACE, foreground=FG, font=heading_font)

    s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(12, 8, 12, 0))
    s.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED, padding=(18, 8),
                borderwidth=0, lightcolor=SURFACE, bordercolor=BG)
    # clam shrinks the selected tab by default; keep its size and lift it slightly instead.
    s.map("TNotebook.Tab", background=[("selected", BG), ("active", FIELD)],
          foreground=[("selected", FG)], padding=[("selected", (18, 8))],
          expand=[("selected", (0, 3, 0, 0))])

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
                bordercolor=BG, lightcolor=ACCENT, darkcolor=ACCENT, gripcount=0,
                sliderlength=18)
    s.map("Horizontal.TScale", background=[("disabled", BORDER), ("active", ACCENT_HOVER)])

    # clam draws a cross in its checkboxes and has no option for a check mark, so both
    # indicators are replaced by drawn images.
    size = round(base.metrics("linespace") * 0.75)
    images = root._theme_images = _indicator_images(root, size)
    for widget, kind in (("TCheckbutton", "check"), ("TRadiobutton", "radio")):
        element = f"Clcr.{widget[1:]}.indicator"
        img = {state: images[kind, state] for state in INDICATOR_STATES}
        s.element_create(element, "image", img["off"],
                         ("disabled", "selected", img["disabled-on"]),
                         ("disabled", img["disabled-off"]),
                         ("active", "selected", img["hover-on"]),
                         ("selected", img["on"]), ("active", img["hover-off"]),
                         width=size + 8, sticky="w")  # 8 px gap before the label
        s.layout(widget, [(f"{widget[1:]}.padding", {"sticky": "nswe", "children": [
            (element, {"side": "left", "sticky": ""}),
            (f"{widget[1:]}.focus", {"side": "left", "sticky": "w", "children": [
                (f"{widget[1:]}.label", {"sticky": "nswe"})]})]})])
        s.configure(widget, background=BG, foreground=FG)
        s.map(widget, foreground=[("disabled", MUTED)], background=[("active", BG)])

    # Variants for widgets placed on a card (see restyle_cards()).
    for style in CARD_STYLES:
        s.configure(f"Card.{style}", background=SURFACE)
    s.configure("Card.Horizontal.TScale", background=ACCENT, bordercolor=SURFACE)
    for widget in ("TCheckbutton", "TRadiobutton"):
        s.map(f"Card.{widget}", background=[("active", SURFACE)])


# Styles that need a card-colored variant; widgets of other types (fields, buttons)
# already look right on a card.
CARD_STYLES = ("TFrame", "TLabel", "Muted.TLabel", "Small.TLabel", "TCheckbutton",
               "TRadiobutton", "Horizontal.TScale")
DEFAULT_STYLES = {"TScale": "Horizontal.TScale"}


def restyle_cards(widget):
    """Give everything inside each Card.TLabelframe under `widget` its card style."""
    for child in widget.winfo_children():
        if isinstance(child, ttk.Labelframe) and child.cget("style") == "Card.TLabelframe":
            _restyle_contents(child)
        else:
            restyle_cards(child)


def _restyle_contents(widget):
    for child in widget.winfo_children():
        cls = child.winfo_class()
        style = child.cget("style") if isinstance(child, ttk.Widget) else ""
        style = style or DEFAULT_STYLES.get(cls, cls)
        if style in CARD_STYLES:
            child.configure(style=f"Card.{style}")
        _restyle_contents(child)


# ---- checkbox and radio button indicators ------------------------------------

# state: (fill, border, mark); None means "not drawn".
INDICATOR_STATES = {
    "off": (FIELD, BORDER, None),
    "hover-off": (FIELD, ACCENT, None),
    "on": (ACCENT, None, "#ffffff"),
    "hover-on": (ACCENT_HOVER, None, "#ffffff"),
    "disabled-off": (SURFACE, BORDER, None),
    "disabled-on": (BORDER, None, MUTED),
}


def _indicator_images(root, size):
    images = {}
    for kind in ("check", "radio"):
        for state, (fill, border, mark) in INDICATOR_STATES.items():
            layers = []
            if border:
                layers.append((border, _shape(kind, size, 0)))
                layers.append((fill, _shape(kind, size, 1)))
            else:
                layers.append((fill, _shape(kind, size, 0)))
            if mark:
                layers.append((mark, _mark(kind, size)))
            data = _png(size, layers)
            images[kind, state] = tk.PhotoImage(master=root, data=data, format="png")
    return images


def _shape(kind, size, inset):
    """The indicator's outline, shrunk by `inset` pixels."""
    c = size / 2
    if kind == "radio":
        r = c - inset
        return lambda x, y: (x - c) ** 2 + (y - c) ** 2 <= r * r
    half, radius = c - inset, max(size * 0.2 - inset, 0.5)
    inner = half - radius

    def inside(x, y):
        dx, dy = max(abs(x - c) - inner, 0), max(abs(y - c) - inner, 0)
        return dx * dx + dy * dy <= radius * radius
    return inside


def _mark(kind, size):
    """A dot for radio buttons, a check mark for checkboxes."""
    c = size / 2
    if kind == "radio":
        r = size * 0.2
        return lambda x, y: (x - c) ** 2 + (y - c) ** 2 <= r * r
    points = [(0.26 * size, 0.52 * size), (0.43 * size, 0.69 * size),
              (0.75 * size, 0.33 * size)]
    half_width = size * 0.07

    def near(x, y):
        return any(_distance(x, y, *a, *b) <= half_width for a, b in zip(points, points[1:]))
    return near


def _distance(x, y, x1, y1, x2, y2):
    """Distance from (x, y) to the segment (x1, y1)-(x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - x1 - t * dx, y - y1 - t * dy)


def _png(size, layers, samples=4):
    """Paint (color, inside(x, y)) layers onto a transparent square and return PNG data.

    Each pixel is sampled samples x samples times, which smooths the edges.
    """
    offsets = [(i + 0.5) / samples for i in range(samples)]
    rows = []
    for py in range(size):
        row = bytearray(b"\0")  # PNG filter type: none
        for px in range(size):
            r = g = b = a = 0.0  # premultiplied by alpha
            for color, inside in layers:
                hits = sum(inside(px + ox, py + oy) for ox in offsets for oy in offsets)
                cover = hits / samples ** 2
                if cover:
                    cr, cg, cb = (int(color[i:i + 2], 16) for i in (1, 3, 5))
                    r = cr * cover + r * (1 - cover)
                    g = cg * cover + g * (1 - cover)
                    b = cb * cover + b * (1 - cover)
                    a = cover + a * (1 - cover)
            if a:
                row += bytes((round(r / a), round(g / a), round(b / a), round(a * 255)))
            else:
                row += bytes(4)
        rows.append(bytes(row))

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(b"".join(rows)))
           + chunk(b"IEND", b""))
    return base64.b64encode(png)
