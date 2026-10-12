"""The control center's own settings in ~/.config/clcr/config.json."""

import json
import os
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "clcr" / "config.json"

DEFAULTS = {
    # The mouse can't report its current lighting, so remember what we last set.
    "mouse": {"zone": "all", "effect": "static", "color": "#00aaff", "period": 4000,
              "brightness": 100, "speed": 50, "persist": True},
    "sync_color": "#ff0000",
}


def load() -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        stored = json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        return cfg
    for key, value in stored.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(value)
        else:
            cfg[key] = value
    return cfg


def save(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2))
    tmp.replace(CONFIG_PATH)
