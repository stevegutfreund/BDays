#!/usr/bin/env python3
"""
JSON-based storage helpers for the Birthday Management System.
All entries live in a single data/entries.json file. Each entry carries an
explicit `calendar` (which Google Calendar it pushes to) and an optional
`family` (display/grouping label — omitted for standalone `private` entries).

A "group" below is what routes still call `family` in URLs
(e.g. /family/smith/..., /family/private/...): an entry belongs to a
group if its `family` matches, or (when it has no `family`) if its
`calendar` matches.
"""

import json
import os
from datetime import datetime
from typing import List, Optional

import settings
from services import config_service

DATA_DIR   = str(settings.DATA_DIR)
DATA_FILE  = os.path.join(DATA_DIR, "entries.json")

VALID_TYPES = ("birthday", "wedding anniversary", "event")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Low-level read / write
# ---------------------------------------------------------------------------

def _load_all() -> List[dict]:
    """Load every entry across all families/calendars."""
    _ensure_data_dir()
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError):
        return []


def _save_all(entries: List[dict]) -> None:
    _ensure_data_dir()
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)  # atomic: a crash mid-write can't truncate entries.json


def _group_of(entry: dict) -> str:
    return (entry.get("family") or entry.get("calendar") or "").lower()


def _in_group(entry: dict, group: str) -> bool:
    return _group_of(entry) == group.lower()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_entry(name: str, date: str, after_shkia: bool, entry_type: str = None) -> Optional[str]:
    """
    Validate an entry's fields.
    Returns an error message string on failure, or None on success.
    """
    name = (name or "").strip()
    if not name:
        return "Name must not be empty."

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return "Date must be a valid date in YYYY-MM-DD format."

    if not isinstance(after_shkia, bool):
        return "Choose whether it was before or after shkia."

    if entry_type is not None and entry_type not in VALID_TYPES:
        return f"Type must be one of: {', '.join(VALID_TYPES)}."

    return None


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def list_entries(group: str) -> List[dict]:
    """Return all entries in a group (family or calendar), sorted by date."""
    entries = [e for e in _load_all() if _in_group(e, group)]
    try:
        entries.sort(key=lambda e: e.get("date", ""))
    except Exception:
        pass
    return entries


def get_entry(group: str, name: str) -> Optional[dict]:
    """Return a single entry by exact name (case-insensitive) within a group."""
    for entry in _load_all():
        if _in_group(entry, group) and entry.get("name", "").lower() == name.lower():
            return entry
    return None


def add_entry(group: str, name: str, date: str, after_shkia: bool,
               entry_type: str, color: str = None) -> dict:
    """
    Add a new entry to a group (family or calendar).
    Raises ValueError if validation fails or name already exists in the group.
    """
    error = validate_entry(name, date, after_shkia, entry_type)
    if error:
        raise ValueError(error)

    entries = _load_all()
    name = " & ".join(n.strip().title() for n in name.split("&"))
    calendar = group.lower()

    for e in entries:
        if _in_group(e, calendar) and e.get("name", "").lower() == name.lower():
            raise ValueError(f"An entry for '{name}' already exists.")

    entry = {"name": name, "date": date, "afterShkia": after_shkia, "type": entry_type,
              "calendar": calendar}
    if calendar != "private":
        entry["family"] = calendar
    if color:
        entry["color"] = color

    entries.append(entry)
    _save_all(entries)
    return entry


def update_entry(group: str, original_name: str, name: str, date: str, after_shkia: bool,
                  entry_type: str, color: str = None) -> dict:
    """
    Replace an existing entry identified by original_name within a group.
    The entry's family/calendar are preserved (edit form only changes
    name/date/afterShkia/type/color).
    Raises ValueError if validation fails or original entry not found.
    """
    error = validate_entry(name, date, after_shkia, entry_type)
    if error:
        raise ValueError(error)

    entries = _load_all()
    name = " & ".join(n.strip().title() for n in name.split("&"))

    idx = None
    for i, e in enumerate(entries):
        if _in_group(e, group) and e.get("name", "").lower() == original_name.lower():
            idx = i
            break

    if idx is None:
        raise ValueError(f"Entry '{original_name}' not found.")

    calendar = entries[idx].get("calendar", group.lower())
    entry = {"name": name, "date": date, "afterShkia": after_shkia, "type": entry_type,
              "calendar": calendar}
    if "family" in entries[idx]:
        entry["family"] = entries[idx]["family"]
    if color:
        entry["color"] = color

    entries[idx] = entry
    _save_all(entries)
    return entry


def delete_entry(group: str, name: str) -> bool:
    """
    Delete an entry by name (case-insensitive) within a group.
    Returns True if something was deleted, False otherwise.
    """
    entries = _load_all()
    new_entries = [e for e in entries
                   if not (_in_group(e, group) and e.get("name", "").lower() == name.lower())]
    if len(new_entries) == len(entries):
        return False
    _save_all(new_entries)
    return True


def delete_all_entries(group: str) -> None:
    """Wipe all entries from a group."""
    entries = [e for e in _load_all() if not _in_group(e, group)]
    _save_all(entries)


# ---------------------------------------------------------------------------
# Family/group discovery
# ---------------------------------------------------------------------------

def list_families() -> List[str]:
    """Return the known groups: every calendar configured in config.json."""
    return sorted(config_service.load_config().get("calendars", {}).keys())


def count_entries(group: str) -> int:
    return len(list_entries(group))


def family_exists(group: str) -> bool:
    return group.lower() in list_families()
