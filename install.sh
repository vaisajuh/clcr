#!/usr/bin/env bash
# Installs the Lighting Control Center for the current user:
# tkinter (if missing), the udev rule for device access, the `clcr` command
# and an app-menu entry. Asks for sudo for the system parts.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

if ! python3 -c 'import tkinter' 2>/dev/null; then
  echo "==> Installing tkinter (python3-tk, needs sudo)"
  sudo apt install -y python3-tk
fi

echo "==> Installing udev rule (needs sudo)"
RULE=/etc/udev/rules.d/70-clcr.rules
if [ -f "$RULE" ] && cmp -s clcr/data/70-clcr.rules "$RULE"; then
  echo "already installed"
else
  sudo install -m 644 clcr/data/70-clcr.rules "$RULE"
  sudo udevadm control --reload-rules
  sudo udevadm trigger --subsystem-match=hidraw
fi

echo "==> Installing clcr"
if command -v pipx >/dev/null; then
  pipx install --force .
elif python3 -m pip --version >/dev/null 2>&1; then
  python3 -m pip install --user --break-system-packages .
else
  # No pip: clcr has no dependencies, so a launcher pointing at this folder is enough.
  mkdir -p ~/.local/bin
  ln -sf "$PWD/clcr-run" ~/.local/bin/clcr
  echo "Installed launcher ~/.local/bin/clcr (keep this folder in place)"
fi

mkdir -p ~/.local/share/applications
install -m 644 clcr/data/clcr.desktop ~/.local/share/applications/clcr.desktop

echo
echo "Done. Run 'clcr' or open \"Lighting Control Center\" from the app menu."
echo "Replug the keyboard and mouse if they aren't found the first time."
