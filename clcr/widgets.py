"""Small reusable widgets."""

import tkinter as tk
from tkinter import colorchooser, ttk


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def rgb_to_hex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


class Debouncer:
    """Calls fn once, `ms` after the last time it was triggered."""

    def __init__(self, widget, ms, fn):
        self._widget, self._ms, self._fn = widget, ms, fn
        self._id = None

    def __call__(self):
        self.cancel()
        self._id = self._widget.after(self._ms, self._fire)

    def cancel(self):
        if self._id is not None:
            self._widget.after_cancel(self._id)
            self._id = None

    def flush(self):
        """Run now if a call is pending."""
        if self._id is not None:
            self.cancel()
            self._fn()

    def _fire(self):
        self._id = None
        self._fn()


class ColorButton(tk.Button):
    """A swatch showing a color; clicking it opens a color picker."""

    def __init__(self, parent, color="#ffffff", command=None, title="Choose a color"):
        super().__init__(parent, width=9, relief="flat", bd=0, highlightthickness=0,
                         cursor="hand2", pady=4, command=self._pick)
        self._command = command
        self._title = title
        self.set(color)

    def set(self, color: str):
        self._color = color.lower()
        r, g, b = hex_to_rgb(self._color)
        fg = "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"
        self.configure(bg=self._color, activebackground=self._color, fg=fg,
                       activeforeground=fg, disabledforeground=fg, text=self._color.upper())

    def get(self) -> str:
        return self._color

    def rgb(self) -> tuple[int, int, int]:
        return hex_to_rgb(self._color)

    def set_enabled(self, enabled: bool):
        self.configure(state="normal" if enabled else "disabled",
                       cursor="hand2" if enabled else "")

    def _pick(self):
        _rgb, chosen = colorchooser.askcolor(self._color, parent=self, title=self._title)
        if chosen:
            self.set(chosen)
            if self._command:
                self._command()


class ValueScale(ttk.Frame):
    """A horizontal slider with a formatted value label next to it."""

    def __init__(self, parent, from_, to, value, fmt=str, command=None, resolution=1):
        super().__init__(parent)
        self._fmt, self._command, self._res = fmt, command, resolution
        self.var = tk.DoubleVar(value=value)
        self.scale = ttk.Scale(self, from_=from_, to=to, variable=self.var,
                               command=self._moved, length=220)
        self.label = ttk.Label(self, width=9, anchor="e", style="Muted.TLabel")
        self.scale.pack(side="left", fill="x", expand=True)
        self.label.pack(side="left", padx=(8, 0))
        self._update_label()

    def get(self):
        v = round(self.var.get() / self._res) * self._res
        return int(round(v)) if float(self._res).is_integer() else round(v, 3)

    def set(self, value):
        # Setting the variable moves the slider without calling `command`.
        self.var.set(value)
        self._update_label()

    def set_enabled(self, enabled: bool):
        self.scale.state(["!disabled"] if enabled else ["disabled"])

    def _moved(self, _value):
        self._update_label()
        if self._command:
            self._command()

    def _update_label(self):
        self.label.configure(text=self._fmt(self.get()))


def percent_of_255(v):
    return f"{round(v * 100 / 255)} %"


def form_row(parent, row, label, widget, **grid):
    """Grid a 'label: widget' row and return the label."""
    lbl = ttk.Label(parent, text=label)
    lbl.grid(row=row, column=0, sticky="w", padx=(0, 16), pady=5)
    grid = {"sticky": "ew", "pady": 5, **grid}
    widget.grid(row=row, column=1, **grid)
    return lbl
