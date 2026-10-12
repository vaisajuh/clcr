"""Case lighting tab: ASUS Aura motherboard/ARGB headers."""

import tkinter as tk
from tkinter import ttk

from .. import devices
from ..widgets import ColorButton, Debouncer, ValueScale, form_row
from .base import DevicePanel

APPLY_DELAY_MS = 200


class CasePanel(DevicePanel):
    title = "Case lighting"
    hint = ("Looking for an ASUS Aura USB LED controller. If access is denied, "
            "run install.sh once.")

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.runner = None
        self.cfg = None
        self._apply_later = Debouncer(self, APPLY_DELAY_MS, self._apply)

    # ---- connection --------------------------------------------------------

    def open_device(self):
        return devices.open_case(self.app.demo)

    def read_initial(self, ctrl):
        from ..backends.aura import config
        from ..backends.aura.core import apply
        from ..backends.aura.effects import EffectRunner

        self.cfg = config.load()
        self.runner = EffectRunner(ctrl)
        last = self.cfg["last"]
        # Hardware modes keep running on the controller by themselves; software
        # effects need someone to draw them, so resume the last one.
        if last.get("kind") == "software":
            try:
                apply(ctrl, self.runner, last)
            except Exception as e:
                return f"Could not resume the last effect: {e}"
        return None

    def before_close(self, ctrl):
        if self.runner:
            self.runner.stop()

    def _save_cfg(self):
        if not self.app.demo:
            from ..backends.aura import config

            config.save(self.cfg)

    # ---- controls ----------------------------------------------------------

    def build(self, body, warning):
        from ..backends.aura.aura import MODES
        from ..backends.aura.effects import EFFECTS

        self.hardware_modes = [m for m in MODES if m != "direct"]
        self.software_effects = list(EFFECTS)
        zones = self.dev.zones
        last = self.cfg["last"]
        self._loading = True

        left = ttk.LabelFrame(body, text="  Lighting  ", padding=(16, 10))
        left.grid(row=0, column=0, sticky="nsew")
        right = ttk.LabelFrame(body, text="  Zones  ", padding=(16, 10))
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)

        self.kind = tk.StringVar(value=last.get("kind", "hardware"))
        kinds = ttk.Frame(left)
        ttk.Radiobutton(kinds, text="Hardware mode", value="hardware", variable=self.kind,
                        command=self._kind_changed).pack(side="left")
        ttk.Radiobutton(kinds, text="Software effect", value="software", variable=self.kind,
                        command=self._kind_changed).pack(side="left", padx=(16, 0))
        form_row(left, 0, "Type", kinds, sticky="w")

        self.mode = ttk.Combobox(left, state="readonly", height=16)
        self.mode.bind("<<ComboboxSelected>>", self._changed)
        form_row(left, 1, "Mode", self.mode)
        self.color = ColorButton(left, last.get("color", "#ff0000"), self._changed,
                                 title="Case lighting color")
        form_row(left, 2, "Color", self.color, sticky="w")
        self.brightness = ValueScale(left, 0, 1, float(last.get("brightness", 1.0)),
                                     lambda v: f"{round(v * 100)} %", self._changed, 0.01)
        form_row(left, 3, "Brightness", self.brightness)
        self.speed = ValueScale(left, 0.1, 5, float(last.get("speed", 1.0)),
                                lambda v: f"{v:.1f}×", self._changed, 0.1)
        self.speed_label = form_row(left, 4, "Speed", self.speed)
        self.note = ttk.Label(left, style="Small.TLabel", wraplength=380, justify="left")
        self.note.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        btns = ttk.Frame(left)
        btns.grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(btns, text="Turn off", command=self.set_off).pack(side="left")
        left.columnconfigure(1, weight=1)

        selected = last.get("zones", ["all"])
        self.zone_vars = {}
        self.led_spins = {}
        for i, z in enumerate(zones):
            var = tk.BooleanVar(value="all" in selected or z.name in selected)
            kind = "ARGB" if z.addressable else "RGB"
            ttk.Checkbutton(right, text=f"{z.name}  ({kind})", variable=var,
                            command=self._changed).grid(row=i, column=0, sticky="w", pady=3)
            self.zone_vars[z.name] = var
            if z.addressable:
                spin = ttk.Spinbox(right, from_=0, to=240, width=5,
                                   command=lambda z=z: self._leds_changed(z))
                spin.set(z.led_count)
                spin.bind("<Return>", lambda _e, z=z: self._leds_changed(z))
                spin.bind("<FocusOut>", lambda _e, z=z: self._leds_changed(z))
                spin.grid(row=i, column=1, sticky="e", padx=(12, 4))
                ttk.Label(right, text="LEDs", style="Muted.TLabel").grid(row=i, column=2, sticky="w")
                self.led_spins[z.name] = spin
        ttk.Label(right, style="Small.TLabel", wraplength=260, justify="left", text=(
            "The controller can't detect how many LEDs are on each ARGB header. "
            "Set the count to match your fans/strips; software effects skip headers "
            "with 0 LEDs.")).grid(row=len(zones), column=0, columnspan=3, sticky="w", pady=(12, 0))
        right.columnconfigure(0, weight=1)

        self._fill_modes(last.get("mode"))
        self._loading = False
        if warning:
            self.app.status(f"{self.title}: {warning}", error=True)

    def _fill_modes(self, current=None):
        software = self.kind.get() == "software"
        names = self.software_effects if software else self.hardware_modes
        self.mode.configure(values=names)
        self.mode.set(current if current in names else ("rainbow-wave" if software else "static"))
        self.speed.set_enabled(software)
        self.note.configure(text=(
            "Software effects are drawn per-LED by this app and stop when it is closed."
            if software else
            "Hardware modes run on the controller and keep going after this app is closed."))

    def _kind_changed(self):
        self._fill_modes()
        self._changed()

    def _leds_changed(self, zone):
        spin = self.led_spins[zone.name]
        try:
            count = max(0, min(240, int(spin.get())))
        except ValueError:
            count = zone.led_count
        spin.set(count)
        if count == zone.led_count:
            return
        zone.led_count = count
        header = zone.name.removeprefix("argb")
        self.cfg["argb_leds"][header] = count
        self._save_cfg()
        if self.kind.get() == "software":
            self._changed()

    def _state(self):
        names = [n for n, v in self.zone_vars.items() if v.get()]
        return {
            "kind": self.kind.get(),
            "mode": self.mode.get(),
            "color": self.color.get(),
            "zones": ["all"] if len(names) == len(self.zone_vars) else names,
            "speed": self.speed.get(),
            "brightness": self.brightness.get(),
        }

    def _changed(self, *_):
        if not self._loading:
            self._apply_later()

    def _apply(self):
        from ..backends.aura.core import apply

        state = self._state()
        if not state["zones"]:
            self.app.status("Case lighting: select at least one zone.", error=True)
            return
        runner = self.runner

        def saved(_result):
            self.cfg["last"] = state
            self._save_cfg()

        self.run(lambda ctrl: apply(ctrl, runner, state), on_done=saved, key="apply")

    def flush(self):
        self._apply_later.flush()

    # ---- overview sync -----------------------------------------------------

    def set_static(self, rgb):
        if self.dev is None or not hasattr(self, "zone_vars"):
            return
        from ..widgets import rgb_to_hex

        self.kind.set("hardware")
        self._fill_modes("static")
        self.color.set(rgb_to_hex(rgb))
        if self.brightness.get() == 0:
            self.brightness.set(1.0)
        for var in self.zone_vars.values():
            var.set(True)
        self._changed()

    def set_off(self):
        if self.dev is None or not hasattr(self, "zone_vars"):
            return
        self.kind.set("hardware")
        self._fill_modes("off")
        self._changed()
