# Contributing to Computer Lighting Control Center

Thanks for helping! clcr's goal is to support as much lighting hardware as
possible, and that only works with people who own the hardware. Every
contribution counts, from a one-line test report to a new driver.

The maintainer can only test the devices on their own desk. Support for
everything else is written and tested by contributors, and merged based on
their test report; see [How device support works](README.md#how-device-support-works).

## Ways to help

- **Test a device.** Tried clcr with a device marked 🟡 in the README, or
  one that isn't listed? [Report how it went](https://github.com/vaisajuh/clcr/issues/new?template=device-report.md).
- **Request a device.** [Open a device request](https://github.com/vaisajuh/clcr/issues/new?template=device-request.md)
  with the details the template asks for.
- **Report a bug.** [Open a bug report](https://github.com/vaisajuh/clcr/issues/new?template=bug-report.md).
- **Write code:** fix a bug, improve the GUI, or add a device.

## Where does a change go?

clcr is one of four repos. The keyboard, case and mouse drivers live in
their own projects, and clcr carries copies of them in `clcr/backends/`.

| You want to change… | Open the pull request in |
| --- | --- |
| The VIA keyboard driver (`clcr/backends/via/`) | [vaisajuh/viactl](https://github.com/vaisajuh/viactl) |
| The ASUS Aura driver (`clcr/backends/aura/`), or a new motherboard brand | [vaisajuh/caselight](https://github.com/vaisajuh/caselight) |
| The Logitech HID++ driver (`clcr/backends/logitech/`) | [vaisajuh/logiled](https://github.com/vaisajuh/logiled) |
| The app: GUI, tabs, settings, install, a new device | [vaisajuh/clcr](https://github.com/vaisajuh/clcr) (here) |

Never edit the files in `clcr/backends/via/`, `aura/` or `logitech/` in
clcr directly. A CI check fails if they differ from upstream, and the next
sync would overwrite the edit anyway.

## How changes flow between the repos

```
 PR in viactl ──▶ merged ──▶ nightly sync in clcr ──▶ PR in clcr ──▶ merged
 (viactl's tests)            (copies changed files,     (review it)
                               runs clcr's tests)
```

1. Open a pull request in the driver repo. Its tests run on the PR.
2. The maintainer merges it.
3. Every night at 03:00 UTC, clcr's **Sync bundled drivers** workflow
   compares `clcr/backends/` with the latest upstream code. If a copied file
   changed, it copies it, runs clcr's tests and opens a pull request titled
   "Update bundled drivers: …". The PR lists the upstream commits and the
   test result. If one is already open, it is updated instead.
4. The maintainer reviews and merges that PR.

To sync right away instead of waiting for the night, go to clcr's
**Actions → Sync bundled drivers → Run workflow**.

If the sync PR says tests failed, the upstream change broke something in
clcr. Push a fix to the `sync/backends` branch before merging.

GitHub doesn't run other workflows on pull requests opened by a workflow,
so the sync PR shows no separate Tests check; the sync workflow runs the
tests itself and reports the result in the PR. To get the usual checks too,
close and reopen the PR.

Which upstream files are copied, and from which commit, is recorded in
[`clcr/backends/sources.json`](clcr/backends/sources.json).

## Development setup

```sh
git clone https://github.com/vaisajuh/clcr.git
cd clcr
./clcr-run --demo                          # emulated devices, safe to click around
python3 -m unittest discover -s tests      # tests, no hardware needed
python3 scripts/sync_backends.py --verify  # bundled drivers are unedited
```

You need Python 3.10+ and tkinter (`sudo apt install python3-tk` on
Debian/Ubuntu). No other packages.

## Adding a new device

A device needs a **driver** (talks to the hardware) and a **tab** (the GUI).

### 1. The driver

- Put it in `clcr/backends/<family>/`, e.g. `backends/corsair/`. It can
  also start as its own repo, like viactl; then add it to
  `clcr/backends/sources.json` so it is synced the same way.
- Use only the Python standard library. Talk to the device through
  `/dev/hidraw*`; see `backends/via/via.py` for how to find a device in
  sysfs by its USB IDs or HID report descriptor.
- Include an **emulated device**, a class with the same methods that keeps
  state in memory (see `backends/via/fake.py` and `FakeMouse` in
  `devices.py`). The tests and `clcr --demo` use it.
- Raise exceptions with messages a user can act on ("Permission denied,
  run install.sh"), not raw error codes.

### 2. The tab

- Add an `open_<family>(demo=False)` function to `clcr/devices.py` that
  returns `(device, display name)`, using the emulated device when `demo`
  is true.
- Create `clcr/panels/<family>.py` with a subclass of `DevicePanel`
  (`panels/base.py`) and implement:
  - `open_device()` and `read_initial(dev)`: run on the device's worker
    thread, so slow I/O is fine here
  - `build(body, info)`: create the controls from what the device reported
  - `set_static(rgb)` and `set_off()`: used by the Overview tab's sync buttons
  - `flush()`, plus `before_close(dev)` if something must stop before closing
- Register the panel in `App.__init__` (`clcr/app.py`) and add a
  one-line description in `panels/overview.py`.

### 3. Access, tests, docs

- Add a udev line for the device's USB vendor ID to
  `clcr/data/70-clcr.rules`.
- Add tests for the protocol encoding and the emulated device to `tests/`.
- Add the device to the **Supported devices** table in the README.

## Getting a driver merged

The maintainer reviews the code but can't test your hardware, so a new or
changed driver needs:

1. **A hardware test report** in the pull request: exact model, USB ID,
   Linux distribution, what works and what doesn't. A short video or photo
   of the lights changing helps. The pull request template has the fields.
2. **An emulated device and tests**, so CI checks the code even without the
   hardware, and so `clcr --demo` shows the tab.
3. **Readable code that only does its job.** A lighting driver reads and
   writes its own `/dev/hidraw*` device and nothing else: no network access,
   no running other programs, no files outside its settings. Reviewers
   check this line by line.
4. **No permanent changes without explanation.** Firmware updates are out
   of scope. Commands that store settings permanently on the device must be
   documented in the code and debounced in the GUI.
5. **Someone to look after it.** After the merge you're listed as the
   driver's maintainer in the README, the device is marked 🤝 community
   tested with your name, and you'll be asked to review future changes to
   your driver. Can't keep doing that? Say so in an issue, no problem.

A driver that breaks, with nobody left who has the hardware to fix it, is
marked unmaintained and may be removed in a later release.

## Ground rules

- **No third-party dependencies.** Standard library and tkinter only.
- **Never block the GUI thread.** All device I/O goes through the panel's
  `run()` / worker thread.
- **Go easy on device memory.** Apply changes live, but debounce writes
  to the device's persistent storage (EEPROM/flash) so a dragged slider
  doesn't write hundreds of times.
- **Only contribute code you may license under MIT.** Reading protocol
  documentation and captures is fine, but don't copy code from projects with
  other licenses (for example OpenRGB, which is GPL). Note where your
  protocol knowledge came from.
- **Be careful with real hardware.** Don't send undocumented commands to
  find out what they do. Some write firmware or settings permanently.
- **Match the surrounding code** in style and naming, and keep pull requests
  focused on one thing.

## Pull request checklist

The [pull request template](.github/pull_request_template.md) has the full
checklist. In short:

- [ ] Tests pass: `python3 -m unittest discover -s tests`
- [ ] Tried in `clcr --demo`, and on real hardware (hardware test report filled in)
- [ ] README updated if devices or behavior changed
- [ ] Driver changes made upstream, not in `clcr/backends/` (see above)

## Maintainer

clcr is maintained by Juha Väisänen ([@vaisajuh](https://github.com/vaisajuh)),
who reviews and merges pull requests. Questions are welcome as issues.

By contributing, you agree that your contribution is licensed under the
project's [MIT License](LICENSE).
