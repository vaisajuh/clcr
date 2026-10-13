"""Logitech mouse tab: lighting, DPI, polling rate, onboard mode."""

import tkinter as tk
from tkinter import ttk

from .. import devices
from ..widgets import ChoiceBox, ColorButton, Debouncer, ValueScale, WrapLabel, form_row, rgb_to_hex
from .base import DevicePanel

APPLY_DELAY_MS = 300
DPI_DELAY_MS = 300


class MousePanel(DevicePanel):
    title = "Mouse"
    hint = ("Looking for a Logitech HID++ mouse. If access is denied, run install.sh "
            "once and replug the mouse. Close Solaar/Piper first.")

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._loading = True
        self._apply_later = Debouncer(self, APPLY_DELAY_MS, self._apply_lighting)
        self._dpi_later = Debouncer(self, DPI_DELAY_MS, self._apply_dpi)

    def open_device(self):
        return devices.open_mouse(self.app.demo)

    def read_initial(self, mouse):
        from ..backends.logitech.hidpp import HIDPPError

        def attempt(fn):
            try:
                return fn()
            except HIDPPError:
                return None

        return {
            "zones": attempt(mouse.zones) or [],
            "dpi": attempt(mouse.dpi),
            "dpi_choices": attempt(mouse.dpi_choices) or [],
            "rate": attempt(mouse.report_rate),
            "rates": attempt(mouse.report_rates) or [],
            "mode": attempt(mouse.mode),
        }

    # ---- controls ------------------------------------------------------------

    def build(self, body, info):
        self._loading = True
        self.zones = info["zones"]
        st = self.app.settings["mouse"]

        light = ttk.LabelFrame(body, text="Lighting", style="Card.TLabelframe",
                               padding=(16, 8, 16, 16))
        light.grid(row=0, column=0, sticky="nsew")
        perf = ttk.LabelFrame(body, text="Performance", style="Card.TLabelframe",
                              padding=(16, 8, 16, 16))
        perf.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        # lighting
        if not self.zones:
            ttk.Label(light, text="This mouse has no controllable lighting.",
                      style="Muted.TLabel").grid(row=0, column=0)
        else:
            self.zone = ChoiceBox(light, ["all"] + [z.name for z in self.zones])
            self.zone.set(st["zone"] if st["zone"] in self.zone.choices else "all")
            self.zone.bind("<<ComboboxSelected>>", self._zone_changed)
            form_row(light, 0, "Zone", self.zone)
            self.effect = ChoiceBox(light)
            self.effect.bind("<<ComboboxSelected>>", self._effect_changed)
            form_row(light, 1, "Effect", self.effect)
            self.color = ColorButton(light, st["color"], self._changed, title="Mouse color")
            self.period = ValueScale(light, 1000, 20000, st["period"],
                                     lambda v: f"{v / 1000:.1f} s", self._changed, 100)
            self.brightness = ValueScale(light, 1, 100, st["brightness"],
                                         lambda v: f"{v} %", self._changed)
            self.speed = ValueScale(light, 0, 255, st["speed"], str, self._changed)
            self.params = {}
            for row, (key, label, widget) in enumerate((
                    ("color", "Color", self.color), ("period", "Period", self.period),
                    ("brightness", "Brightness", self.brightness),
                    ("speed", "Speed", self.speed)), start=2):
                lbl = form_row(light, row, label, widget,
                               sticky="w" if key == "color" else "ew")
                self.params[key] = (lbl, widget)
            self.persist = tk.BooleanVar(value=st["persist"])
            ttk.Checkbutton(light, text="Save to mouse memory (survives replugging)",
                            variable=self.persist, command=self._changed).grid(
                row=6, column=0, columnspan=2, sticky="w", pady=(10, 0))
            btns = ttk.Frame(light)
            btns.grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 0))
            ttk.Button(btns, text="Turn off", command=self.set_off).pack(side="left")
            light.columnconfigure(1, weight=1)
            self._fill_effects(st["effect"])

        # performance
        row = 0
        choices = info["dpi_choices"]
        self.dpi_choices = choices
        if info["dpi"] is not None and choices:
            self.dpi = ValueScale(perf, choices[0], choices[-1], info["dpi"],
                                  lambda v: f"{self._snap_dpi(v)} DPI", self._dpi_later)
            form_row(perf, row, "DPI", self.dpi)
            row += 1
        if info["rate"] is not None and info["rates"]:
            self.rate = ttk.Combobox(perf, state="readonly", width=10,
                                     values=[f"{r} Hz" for r in info["rates"]])
            self.rate.set(f"{info['rate']} Hz")
            self.rate.bind("<<ComboboxSelected>>", self._apply_rate)
            form_row(perf, row, "Polling rate", self.rate, sticky="w")
            row += 1
        if info["mode"] is not None:
            self.mode = ChoiceBox(perf, ["onboard", "host"], width=10)
            self.mode.set(info["mode"])
            self.mode.bind("<<ComboboxSelected>>", self._apply_mode)
            form_row(perf, row, "Mode", self.mode, sticky="w")
            row += 1
            WrapLabel(perf, style="Small.TLabel", text=(
                "Onboard: the mouse uses its stored profiles, which may override DPI and "
                "rate. Host: this app is in control until the mouse is unplugged.")).grid(
                row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
            row += 1
        if row == 0:
            ttk.Label(perf, text="No adjustable settings found.", style="Muted.TLabel").grid()
        perf.columnconfigure(1, weight=1)
        self._loading = False

    def _selected_zones(self):
        name = self.zone.get()
        return self.zones if name == "all" else [z for z in self.zones if z.name == name]

    def _fill_effects(self, current=None):
        from ..backends.logitech.device import EFFECT_PARAMS

        zones = self._selected_zones()
        names = [e for e in EFFECT_PARAMS if all(e in z.effects for z in zones)]
        self.effect.set_choices(names)
        current = current or self.effect.get()
        self.effect.set(current if current in names else (names[0] if names else ""))
        self._show_params()

    def _show_params(self):
        from ..backends.logitech.device import EFFECT_PARAMS

        used = EFFECT_PARAMS.get(self.effect.get(), ())
        for key, (lbl, widget) in self.params.items():
            if key in used:
                lbl.grid()
                widget.grid()
            else:
                lbl.grid_remove()
                widget.grid_remove()

    def _zone_changed(self, *_):
        self._fill_effects()
        self._changed()

    def _effect_changed(self, *_):
        self._show_params()
        self._changed()

    def _changed(self, *_):
        if not self._loading:
            self._apply_later()

    def _apply_lighting(self):
        effect = self.effect.get()
        if not effect:
            return
        zones = self._selected_zones()
        persist = self.persist.get()
        params = {"color": self.color.rgb(), "period": self.period.get(),
                  "brightness": self.brightness.get(), "speed": self.speed.get()}
        self.app.settings["mouse"].update(
            zone=self.zone.get(), effect=effect, color=self.color.get(), persist=persist,
            period=params["period"], brightness=params["brightness"], speed=params["speed"])
        self.app.save_settings()

        def work(mouse):
            for z in zones:
                mouse.set_effect(z, effect, persist=persist, **params)

        self.run(work, key="lighting")

    def _snap_dpi(self, value):
        if not self.dpi_choices:
            return value
        return min(self.dpi_choices, key=lambda c: abs(c - value))

    def _apply_dpi(self):
        value = self._snap_dpi(self.dpi.get())
        self.run(lambda m: m.set_dpi(value), on_done=self.dpi.set, key="dpi")

    def _apply_rate(self, *_):
        hz = int(self.rate.get().split()[0])
        self.run(lambda m: m.set_report_rate(hz), key="rate")

    def _apply_mode(self, *_):
        mode = self.mode.get()
        self.run(lambda m: m.set_mode(mode), key="mode")

    def flush(self):
        self._apply_later.flush()
        self._dpi_later.flush()

    # ---- overview sync -----------------------------------------------------

    def _lighting_ready(self):
        return self.dev is not None and getattr(self, "zones", None) and hasattr(self, "effect")

    def set_static(self, rgb):
        if not self._lighting_ready():
            return
        self.zone.set("all")
        self._fill_effects("static")
        self.color.set(rgb_to_hex(rgb))
        self._changed()

    def set_off(self):
        if not self._lighting_ready():
            return
        self.zone.set("all")
        self._fill_effects("off")
        self._changed()
