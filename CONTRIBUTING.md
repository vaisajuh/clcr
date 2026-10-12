# Contributing to Computer Lighting Control Center

Thanks for helping! clcr's goal is to support as much lighting hardware as
possible, and that only works with people who own the hardware. Every
contribution counts, from a one-line test report to a new driver.

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
| The Akko / VIA keyboard driver (`clcr/backends/akko/`) | [vaisajuh/akkoctl](https://github.com/vaisajuh/akkoctl) |
| The ASUS Aura driver (`clcr/backends/aura/`) | [vaisajuh/caselight](https://github.com/vaisajuh/caselight) |
| The Logitech HID++ driver (`clcr/backends/logitech/`) | [vaisajuh/logiled](https://github.com/vaisajuh/logiled) |
| The app: GUI, tabs, settings, install, a new device | [vaisajuh/clcr](https://github.com/vaisajuh/clcr) (here) |

Never edit the files in `clcr/backends/akko/`, `aura/` or `logitech/` in
clcr directly. A CI check fails if they differ from upstream, and the next
sync would overwrite the edit anyway.

## How changes flow between the repos

```
 PR in akkoctl ──▶ merged ──▶ nightly sync in clcr ──▶ PR in clcr ──▶ merged
 (akkoctl's tests)            (copies changed files,     (review it)
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
  also start as its own repo, like akkoctl; then add it to
  `clcr/backends/sources.json` so it is synced the same way.
- Use only the Python standard library. Talk to the device through
  `/dev/hidraw*`; see `backends/akko/via.py` for how to find a device in
  sysfs by its USB IDs or HID report descriptor.
- Include an **emulated device**, a class with the same methods that keeps
  state in memory (see `backends/akko/fake.py` and `FakeMouse` in
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

- [ ] Tests pass: `python3 -m unittest discover -s tests`
- [ ] Tried in `clcr --demo`, and on real hardware if you have it (say which)
- [ ] README updated if devices or behavior changed
- [ ] Driver changes made upstream, not in `clcr/backends/` (see above)

## Maintainer

clcr is maintained by Juha Väisänen ([@vaisajuh](https://github.com/vaisajuh)),
who reviews and merges pull requests. Questions are welcome as issues.

By contributing, you agree that your contribution is licensed under the
project's [MIT License](LICENSE).
