"""Opens the device drivers in clcr/backends/, or emulated devices for --demo."""

from .backends.aura import config as aura_config
from .settings import CONFIG_PATH

# The bundled caselight driver keeps its settings next to clcr's own instead
# of in ~/.config/caselight/. Set here so backends/ stays identical to upstream.
aura_config.CONFIG_PATH = CONFIG_PATH.with_name("caselight.json")



def open_keyboard(demo=False):
    """Return (VIA Keyboard, display name)."""
    from .backends.akko import via

    if demo:
        from .backends.akko.fake import fake_keyboard

        return fake_keyboard(), "Akko 5075B Plus-S (demo)"
    found = via.find_devices()
    kb = via.Keyboard.open()
    return kb, found[0]["name"] if found else "VIA keyboard"


def open_case(demo=False):
    """Return (AuraController, display name)."""
    from .backends.aura import config
    from .backends.aura.aura import AuraController

    leds = config.argb_leds(config.load())
    ctrl = FakeAura(leds) if demo else AuraController(None, leds)
    return ctrl, f"ASUS Aura controller ({ctrl.info.firmware})"


def open_mouse(demo=False):
    """Return (Mouse, display name)."""
    from .backends.logitech.device import Mouse

    mouse = FakeMouse() if demo else Mouse.open()
    return mouse, mouse.name()


# ---- emulated devices ------------------------------------------------------

def _fake_aura_class():
    from .backends.aura.aura import AuraController, DeviceInfo, Zone

    class _FakeAura(AuraController):
        """AuraController that drops writes instead of sending them to hardware."""

        def __init__(self, argb_leds):
            self.info = DeviceInfo(path="/dev/demo", firmware="AULA3-DEMO", zones=[
                Zone("mainboard", 0, 0x04, 3, 0),
                Zone("argb1", 1, 0, argb_leds.get(1, 0), 3, addressable=True),
                Zone("argb2", 2, 1, argb_leds.get(2, 0), 4, addressable=True),
            ])

        def _write(self, packet):
            pass

        def close(self):
            pass

    return _FakeAura


def FakeAura(argb_leds):
    return _fake_aura_class()(argb_leds)


class FakeMouse:
    """Stand-in for backends.logitech.device.Mouse that mirrors a G502 HERO."""

    devnode = "/dev/demo"

    def __init__(self):
        from .backends.logitech.device import Zone

        effects = {"off": 0, "static": 1, "cycle": 2, "breathe": 3}
        self._zones = [Zone(0, 0x0001, dict(effects)), Zone(1, 0x0002, dict(effects))]
        self._dpi, self._rate, self._mode = 1600, 1000, "onboard"
        self.applied = {}

    def name(self):
        return "G502 HERO Gaming Mouse (demo)"

    def close(self):
        pass

    def zones(self):
        return self._zones

    def set_effect(self, zone, effect, persist=True, **params):
        from .backends.logitech.device import effect_params

        if effect not in zone.effects:
            raise ValueError(f"zone {zone.name} does not support {effect!r}")
        effect_params(effect, **params)
        self.applied[zone.name] = (effect, params, persist)

    def dpi_choices(self, sensor=0):
        return list(range(100, 25601, 50))

    def dpi(self, sensor=0):
        return self._dpi

    def set_dpi(self, value, sensor=0):
        choices = self.dpi_choices()
        self._dpi = min(choices, key=lambda c: abs(c - value))
        return self._dpi

    def report_rates(self):
        return [1000, 500, 250, 125]

    def report_rate(self):
        return self._rate

    def set_report_rate(self, hz):
        self._rate = hz

    def mode(self):
        return self._mode

    def set_mode(self, mode):
        self._mode = mode
