---
name: Device request
about: Ask for support for a lighting device clcr doesn't handle yet
title: "Device request: <brand> <model>"
labels: device-request
---

**Device:** brand and exact model (e.g. Corsair K70 RGB PRO)

**Type:** keyboard / mouse / headset / motherboard / fan hub / GPU / RAM / other

**USB ID:** output of `lsusb` for the device (the `xxxx:xxxx` part)

```
paste lsusb line here
```

**HID interfaces:** output of
`for d in /sys/class/hidraw/*; do echo "$d $(grep HID_NAME $d/device/uevent)"; done`

```
paste here
```

**What should be controllable?** colors, effects, zones, DPI, …

**Known protocol documentation or other Linux tools that support it**
(links welcome, e.g. OpenRGB's device list):

**Can you test changes on this device?** yes / no
