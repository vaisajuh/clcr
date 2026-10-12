"""Overview tab: status of every device plus one-click sync for all of them."""

from tkinter import ttk

from ..theme import STATUS_COLORS
from ..widgets import ColorButton

DESCRIPTIONS = {
    "Keyboard": "VIA keyboards: per-key backlight and sidelights",
    "Case lighting": "ASUS Aura motherboard and ARGB headers",
    "Mouse": "Logitech G502 lighting, DPI and polling rate",
}


class OverviewPanel(ttk.Frame):
    def __init__(self, parent, app, panels):
        super().__init__(parent, padding=(20, 16))
        self.app = app
        self.panels = panels
        self.cards = {}

        ttk.Label(self, text="Computer Lighting Control Center", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text="All your computer lighting in one place.", style="Muted.TLabel").pack(
            anchor="w", pady=(2, 16))

        cards = ttk.Frame(self)
        cards.pack(fill="x")
        for col, panel in enumerate(panels):
            card = ttk.Frame(cards, style="Card.TFrame", padding=16)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 12, 0))
            cards.columnconfigure(col, weight=1, uniform="cards")
            ttk.Label(card, text=panel.title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(card, text=DESCRIPTIONS.get(panel.title, ""), style="CardMuted.TLabel",
                      wraplength=200, justify="left").pack(anchor="w", pady=(2, 10))
            status = ttk.Label(card, style="CardOff.TLabel", wraplength=200, justify="left")
            status.pack(anchor="w")
            ttk.Button(card, text="Open", command=lambda p=panel: app.show(p)).pack(
                anchor="w", pady=(12, 0))
            self.cards[panel] = status

        sync = ttk.LabelFrame(self, text="  Sync all devices  ", padding=(16, 12))
        sync.pack(fill="x", pady=(20, 0))
        ttk.Label(sync, text="Color").grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.color = ColorButton(sync, app.settings.get("sync_color", "#ff0000"),
                                 self._color_picked, title="Color for all devices")
        self.color.grid(row=0, column=1, sticky="w")
        ttk.Button(sync, text="Apply solid color to all", style="Accent.TButton",
                   command=self.sync_color).grid(row=0, column=2, padx=(16, 0))
        ttk.Button(sync, text="All lights off", command=self.all_off).grid(
            row=0, column=3, padx=(8, 0))
        ttk.Label(sync, style="Small.TLabel", text=(
            "Sets every connected device to a static color. Fine-tune each device "
            "on its own tab.")).grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))

        for panel in panels:
            self.update_card(panel)

    def update_card(self, panel):
        label = self.cards.get(panel)
        if label is None:
            return
        state = panel.state if panel.state in STATUS_COLORS else "off"
        text = {
            "ok": f"● Connected\n{panel.device_name}",
            "pending": "● Connecting…",
            "error": "● " + panel.state_text.lstrip("● "),
            "off": "● Not connected",
        }[state]
        label.configure(text=text, style=f"Card{state.title()}.TLabel")

    def _color_picked(self):
        self.app.settings["sync_color"] = self.color.get()
        self.app.save_settings()

    def sync_color(self):
        rgb = self.color.rgb()
        for panel in self.panels:
            panel.set_static(rgb)
        self.app.status(f"Applied {self.color.get().upper()} to all connected devices.")

    def all_off(self):
        for panel in self.panels:
            panel.set_off()
        self.app.status("Turned all lights off.")
