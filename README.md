# Computer Lighting Control Center (clcr)

One desktop app for all the RGB lighting in and around your computer:
keyboards, mice, case fans, motherboards and more, whatever the brand.

[![Tests](https://github.com/vaisajuh/clcr/actions/workflows/tests.yml/badge.svg)](https://github.com/vaisajuh/clcr/actions/workflows/tests.yml)

Most lighting hardware ships with its own Windows-only app, one per brand.
clcr aims to be a single, lightweight control center for all of it on Linux:

- **One window** for every device, plus one-click "same color everywhere".
- **No dependencies.** Pure Python 3 standard library plus tkinter. No
  daemon, no browser, no vendor software. Drivers talk to the hardware
  directly through Linux hidraw.
- **Open and extensible.** Each device family is a small, self-contained
  driver, so adding a brand doesn't mean touching the rest. See
  [Contributing](#contributing).

It currently supports three devices and is meant to grow to cover most
lighting hardware on the market.

## Supported devices

| Type | Brand | Device | Status |
| --- | --- | --- | --- |
| Keyboard | Akko | 5075B Plus-S: per-key backlight, sidelights | ✅ Tested |
| Keyboard | Any | VIA/QMK keyboards with RGB matrix | 🟡 Should work |
| Motherboard / ARGB | ASUS | Aura USB controller, TUF GAMING B550-PLUS (`0b05:1939`) | ✅ Tested |
| Motherboard / ARGB | ASUS | Other Aura USB mainboard controllers (`1867`, `1872`, `18a3`, `18a5`, `18f3`, `19af`, `1aa6`) | 🟡 Should work |
| Mouse | Logitech | G502 (SE) HERO: lighting, DPI, polling rate, onboard mode | ✅ Tested |
| Mouse | Logitech | Other HID++ 2.0 mice with RGB (`0x8070`) | 🟡 Should work |

✅ tested on real hardware · 🟡 same protocol, not yet confirmed. If you try one,
please [report how it went](https://github.com/vaisajuh/clcr/issues/new?template=device-report.md).

Want your device supported? [Open a device request](https://github.com/vaisajuh/clcr/issues/new?template=device-request.md),
or add it yourself: [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-new-device)
explains how.

## Setup

```sh
git clone https://github.com/vaisajuh/clcr.git
cd clcr
./install.sh
```

This installs tkinter (`python3-tk`) if missing, a udev rule so your user can
access the devices without root (`/etc/udev/rules.d/70-clcr.rules`), the `clcr`
command and a "Computer Lighting Control Center" app-menu entry. Replug your
devices afterwards if they aren't found.

## Run

```sh
clcr                # or ./clcr-run from this folder
clcr --demo         # emulated devices, no hardware is touched
```

The **Overview** tab shows which devices are connected and can set every
device to one solid color, or turn all lights off, in one click. Each device
also has its own tab with everything it supports.

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
  A nightly workflow keeps the copies up to date (see
  [Contributing](CONTRIBUTING.md#how-changes-flow-between-the-repos)).
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

## Roadmap

Ideas, roughly in order. Help with any of them is welcome.

- A device registry, so new drivers plug in without editing `app.py`
- More brands: Corsair, Razer, SteelSeries, HyperX, NZXT, Lian Li, MSI and
  Gigabyte motherboards, GPU and RAM lighting
- Lighting profiles and scenes, saved and switched in one click
- Effects synced across all devices
- Packaging: PyPI, Flatpak, distro packages

## Contributing

Contributions are very welcome: bug reports, device test reports, new
device support and code.

- **Report a bug or request a device:** [open an issue](https://github.com/vaisajuh/clcr/issues/new/choose).
- **Change the keyboard, case or mouse driver:** open a pull request in
  [akkoctl](https://github.com/vaisajuh/akkoctl),
  [caselight](https://github.com/vaisajuh/caselight) or
  [logiled](https://github.com/vaisajuh/logiled). Merged changes reach clcr
  automatically.
- **Change the app, or add a new device:** open a pull request here.

[CONTRIBUTING.md](CONTRIBUTING.md) explains the workflow, how to add a device
and the few ground rules.

## Development

```sh
python3 -m unittest discover -s tests
python3 scripts/sync_backends.py --verify   # bundled drivers are unedited
clcr --demo
```

## Maintainer

Maintained by **Juha Väisänen** ([@vaisajuh](https://github.com/vaisajuh)).
Questions, ideas and bug reports are welcome as
[GitHub issues](https://github.com/vaisajuh/clcr/issues).

## Related projects

Part of a small set of Linux lighting tools, all pure Python with no third-party dependencies:

- **clcr** (this repo): Computer Lighting Control Center, one desktop app for lighting across brands and devices (bundles the drivers below)
- [akkoctl](https://github.com/vaisajuh/akkoctl): Akko 5075B Plus-S keyboard: RGB backlight, sidelights, keymap and macros
- [caselight](https://github.com/vaisajuh/caselight): ASUS Aura USB controller: motherboard and ARGB header lighting
- [logiled](https://github.com/vaisajuh/logiled): Logitech G502 HERO mouse: lighting, DPI, polling rate and onboard mode

## Acknowledgements

The ASUS Aura protocol follows the documentation of the
[OpenRGB](https://openrgb.org) project.

## License

MIT. See [LICENSE](LICENSE).
