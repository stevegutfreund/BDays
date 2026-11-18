#!/usr/bin/env python3
"""
Calendar-mapping configuration (config.json): which Google calendar each
family pushes to, and event colours.

    {
      "calendars":   {"<family>": "<google calendar id>", ...},
      "colors":      {"<family>": "<colorId>", ...},
      "type_colors": {"<entry type>": "<colorId>", ...}
    }

The file is git-ignored; ``config.example.json`` shows the shape.
"""

import json
import os
from typing import List, Optional

import settings

CONFIG_FILE = settings.CONFIG_FILE

DEFAULT_COLOR = "11"

_EMPTY = {"calendars": {}, "colors": {}, "type_colors": {}}


def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return json.loads(json.dumps(_EMPTY))


def save_config(cfg: dict) -> None:
    tmp = f"{CONFIG_FILE}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, CONFIG_FILE)


def get_calendar_id(family: str) -> Optional[str]:
    return load_config().get("calendars", {}).get(family.lower())


def get_color(family: str, default: Optional[str] = DEFAULT_COLOR) -> Optional[str]:
    return load_config().get("colors", {}).get(family.lower(), default)


def get_type_color(entry_type: str) -> Optional[str]:
    return load_config().get("type_colors", {}).get(entry_type)


def set_calendar_mapping(family: str, calendar_id: str, color: str = None) -> None:
    cfg = load_config()
    cfg.setdefault("calendars", {})[family.lower()] = calendar_id
    if color:
        cfg.setdefault("colors", {})[family.lower()] = color
    save_config(cfg)


def list_calendar_configs() -> List[dict]:
    cfg = load_config()
    calendars = cfg.get("calendars", {})
    colors    = cfg.get("colors", {})
    return [
        {
            "family":      fam,
            "calendar_id": cid,
            "color":       colors.get(fam, DEFAULT_COLOR),
        }
        for fam, cid in calendars.items()
    ]
