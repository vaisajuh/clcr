"""Keyboard tab: key backlight and sidelights of VIA keyboards."""

from tkinter import ttk

from .. import devices
from ..widgets import ColorButton, Debouncer, ValueScale, form_row, percent_of_255, rgb_to_hex
from .base import DevicePanel

APPLY_DELAY_MS = 120
SAVE_DELAY_MS = 1500   # wait for the user to settle before writing EEPROM


class KeyboardPanel(DevicePanel):
    title = "Keyboard"
    hint = ("Connect the keyboard by USB cable and switch it to wired mode. "
            "If access is denied, run install.sh once and replug it.")

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.editors = []

    def open_device(self):
        return devices.open_keyboard(self.app.demo)

    def read_initial(self, kb):
        from ..backends.via import via

        state = {}
        for zone in ("keys", "side"):
            try:
                state[zone] = kb.get_lighting(via.ZONES[zone][0])
            except via.ViaError as e:
                state[zone] = e
        return state

    def build(self, body, info):
        self.editors = []
        for col, (zone, label) in enumerate((("keys", "Key backlight"), ("side", "Sidelights"))):
            editor = ZoneEditor(body, self, zone, label, info[zone])
            editor.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
            body.columnconfigure(col, weight=1, uniform="zones")
            self.editors.append(editor)
        ttk.Label(body, style="Small.TLabel", text=(
            "Changes apply instantly and are saved to the keyboard after a moment.")).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(14, 0))

    def set_static(self, rgb):
        for e in self.editors:
            e.set_static(rgb)

    def set_off(self):
        for e in self.editors:
            e.set_off()

    def flush(self):
        for e in self.editors:
            e.flush()


class ZoneEditor(ttk.LabelFrame):
    def __init__(self, parent, panel, zone, label, state):
        from ..backends.via import via

        super().__init__(parent, text=f"  {label}  ", padding=(16, 10))
        self.via = via
        self.panel = panel
        self.channel, self.effects, self.no_color = via.ZONES[zone]
        self._sent = {}
        self._apply_later = Debouncer(self, APPLY_DELAY_MS, self._apply)
        self._save_later = Debouncer(self, SAVE_DELAY_MS, self._save)

        self.effect = ttk.Combobox(self, values=self.effects, state="readonly", height=20)
        self.effect.bind("<<ComboboxSelected>>", self._changed)
        form_row(self, 0, "Effect", self.effect)
        self.color = ColorButton(self, command=self._changed, title=f"{label} color")
        form_row(self, 1, "Color", self.color, sticky="w")
        self.brightness = ValueScale(self, 0, 255, 255, percent_of_255, self._changed)
        form_row(self, 2, "Brightness", self.brightness)
        self.speed = ValueScale(self, 0, 255, 128, percent_of_255, self._changed)
        form_row(self, 3, "Speed", self.speed)
        self.note = ttk.Label(self, style="Small.TLabel", wraplength=300)
        self.note.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        btns = ttk.Frame(self)
        btns.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(btns, text="Turn off", command=self.set_off).pack(side="left")
        self.columnconfigure(1, weight=1)

        if isinstance(state, Exception):
            for w in (self.effect, self.brightness, self.speed, self.color):
                (w.set_enabled(False) if hasattr(w, "set_enabled") else w.state(["disabled"]))
            self.note.configure(text=f"Not available: {state}")
            self._enabled = False
            return
        self._enabled = True
        effect = state["effect"]
        self.effect.current(effect if effect < len(self.effects) else 0)
        self.brightness.set(state["brightness"])
        self.speed.set(state["speed"])
        self.color.set(rgb_to_hex(via.hue_sat_to_rgb(*state["color"])))
        self._sent = dict(state)
        self._update_note()

    def _values(self):
        return {
            "effect": max(0, self.effect.current()),
            "brightness": self.brightness.get(),
            "speed": self.speed.get(),
            "color": self.via.rgb_to_hue_sat(*self.color.rgb()),
        }

    def _update_note(self):
        idx = self.effect.current()
        if idx in self.no_color and idx != 0:
            self.note.configure(text="This effect uses its own colors.")
        else:
            self.note.configure(text="")

    def _changed(self, *_):
        if not self._enabled:
            return
        self._update_note()
        self._apply_later()

    def _apply(self):
        values = self._values()
        changed = {k: v for k, v in values.items() if self._sent.get(k) != v}
        if not changed:
            return
        self._sent.update(changed)
        ch = self.channel

        def work(kb):
            if "effect" in changed:
                kb.set_effect(changed["effect"], ch)
            if "brightness" in changed:
                kb.set_brightness(changed["brightness"], ch)
            if "speed" in changed:
                kb.set_speed(changed["speed"], ch)
            if "color" in changed:
                kb.set_color(*changed["color"], channel=ch)

        self.panel.run(work)
        self._save_later()

    def _save(self):
        ch = self.channel
        self.panel.run(lambda kb: kb.save_lighting(ch), key=f"save-{ch}")

    def flush(self):
        self._apply_later.flush()
        self._save_later.flush()

    def set_static(self, rgb):
        if not self._enabled:
            return
        self.effect.current(1)  # Solid Color
        self.color.set(rgb_to_hex(rgb))
        if self.brightness.get() == 0:
            self.brightness.set(255)
        self._changed()

    def set_off(self):
        if not self._enabled:
            return
        self.effect.current(0)
        self._changed()
