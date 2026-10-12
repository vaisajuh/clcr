## What does this change?



## Hardware test report

Required for new or changed device support. The maintainer can't test your
hardware, so this report is what the merge is based on. Not a device change?
Write "n/a".

- Device (brand, exact model):
- USB ID (from `lsusb`):
- Linux distribution and kernel (`uname -r`):
- What you tested, and the result:
- What doesn't work yet:
- Photo or video of the lights (optional, but helpful):

## Checklist

- [ ] Tests pass: `python3 -m unittest discover -s tests`
- [ ] Tried in `clcr --demo`
- [ ] A new or changed driver comes with an emulated device and tests
- [ ] Only the Python standard library; the driver talks only to its own device
- [ ] No commands that change firmware or settings permanently (or they are documented and explained)
- [ ] Driver changes for `clcr/backends/via/`, `aura/` or `logitech/` were made in the upstream repo instead
- [ ] README updated (supported devices table, driver maintainers)
- [ ] I may license this contribution under MIT, and didn't copy code from projects with other licenses
