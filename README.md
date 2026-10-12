# Lighting Control Center (clcr)

One desktop app (tkinter, no browser) for all the lighting on this PC:

| Tab | Device |
| --- | --- |
| **Keyboard** | Akko 5075B Plus-S (or other VIA keyboards): key backlight and sidelights |
| **Case lighting** | ASUS Aura USB controller: motherboard + ARGB headers |
| **Mouse** | Logitech G502 HERO (or other HID++ mice): lighting, DPI, polling rate, mode |

Self-contained: pure Python 3 standard library plus tkinter. The device drivers
are bundled in `clcr/backends/` and talk to the hardware directly through
Linux hidraw.

The **Overview** tab shows which devices are connected and can set every
device to one solid color, or turn all lights off, in one click.

## Setup

```sh
./install.sh
```

This installs tkinter (`python3-tk`) if missing, a udev rule so your user can
access the devices without root (`/etc/udev/rules.d/70-clcr.rules`), the `clcr`
command and a "Lighting Control Center" app-menu entry. Replug the keyboard
and mouse afterwards if they aren't found.

## Run

```sh
clcr                # or ./clcr-run from this folder
clcr --demo         # emulated devices, no hardware is touched
```

## Notes

- Changes apply live. The keyboard writes to its EEPROM about 1.5 s after
  you stop adjusting.
- Case **hardware modes** keep running after the app closes. **Software
  effects** are drawn by the app, so they stop (freeze) when you close it.
  The last software effect resumes the next time the app opens. Don't run
  another Aura tool (OpenRGB, `caselight serve`) at the same time, or they
  will fight over the LEDs.
- The mouse can't report its current lighting, so the Mouse tab shows the
  settings you last applied (stored in `~/.config/clcr/config.json`).
- Settings live in `~/.config/clcr/` (`config.json`, and `caselight.json` for
  ARGB LED counts and the last case lighting).
- The keyboard must be connected by USB cable in wired mode.

## How it's built

```
 tkinter main thread             one worker thread per device         hardware (hidraw)
 ┌────────────────┐   submit()   ┌──────────────────────┐            ┌──────────────┐
 │ Overview tab   │ ───────────▶ │ DeviceWorker          │ ─────────▶ │ Akko keyboard│
 │ Keyboard tab   │              │  job queue,           │            │ ASUS Aura    │
 │ Case tab       │ ◀─────────── │  stale jobs dropped   │ ◀───────── │ G502 mouse   │
 │ Mouse tab      │   post()     └──────────────────────┘            └──────────────┘
 └────────────────┘
```

- **No dependencies.** Everything is the Python 3 standard library plus
  tkinter. The device drivers in `clcr/backends/` read and write
  `/dev/hidrawN` directly, so no libusb, hidapi or daemon is needed.
- **Drivers come from the single-device projects.** `backends/akko` is
  `via.py` and `fake.py` from [akkoctl](https://github.com/vaisajuh/akkoctl),
  `backends/aura` is `aura.py`, `core.py`, `effects.py` and `config.py` from
  [caselight](https://github.com/vaisajuh/caselight), and `backends/logitech` is
  `hidpp.py` and `device.py` from [logiled](https://github.com/vaisajuh/logiled).
  They are copied in, not imported, so clcr installs and runs on its own.
  Protocol details are explained in those repos' READMEs.
- **The GUI never waits for USB.** Tk may only be used from the main thread,
  and a slow or unplugged device could otherwise freeze the window. Each
  device gets its own `DeviceWorker` thread (`worker.py`); results and errors
  come back through a queue that the main loop drains every 30 ms. One
  device failing never blocks the others.
- **Sliders don't flood the device.** Changes go through a `Debouncer`
  (120–300 ms), and jobs submitted with the same key replace older queued ones.
  Writes to the devices' memory are delayed further (the keyboard saves to
  EEPROM 1.5 s after you stop), which also saves flash wear.
- **Tabs adapt to the device.** `panels/base.py` handles connecting,
  reconnecting and error states. Each tab builds its controls from what the
  device reports: keyboard zones and current settings, the Aura zone list,
  and the mouse's lighting zones, supported effects, DPI values and rates.
- **Demo mode.** `devices.py` can return emulated devices instead of real
  ones (`clcr --demo`), which the tests also use.
- **Look.** A dark theme on top of ttk's `clam` theme (`theme.py`).

Layout: `clcr/app.py` (window), `clcr/panels/` (one tab per device),
`clcr/worker.py`, `clcr/devices.py`, `clcr/backends/`, `clcr/widgets.py`
(color button, labelled slider, debouncer).

## Development

```sh
python3 -m unittest discover -s tests
clcr --demo
```

## Related projects

Part of a small set of Linux lighting tools, all pure Python with no third-party dependencies:

- **clcr** (this repo): Lighting Control Center: one tkinter desktop app for all three devices below (bundles their drivers)
- [akkoctl](https://github.com/vaisajuh/akkoctl): Akko 5075B Plus-S keyboard: RGB backlight, sidelights, keymap and macros
- [caselight](https://github.com/vaisajuh/caselight): ASUS Aura USB controller: motherboard and ARGB header lighting
- [logiled](https://github.com/vaisajuh/logiled): Logitech G502 HERO mouse: lighting, DPI, polling rate and onboard mode

## License

MIT. See [LICENSE](LICENSE).
