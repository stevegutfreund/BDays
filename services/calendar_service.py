#!/usr/bin/env python3
"""
Google Calendar sync for BDays: writes each entry as yearly Gregorian and
Hebrew-calendar all-day events, and removes them again.

Transport/auth live in calendarkit.gcal; Hebrew-date rules (shkia, Adar) in
calendarkit.hebrew. This module only holds BDays' event naming and colouring.
"""

import logging
from datetime import date, datetime
from typing import Optional

from calendarkit import hebrew
from calendarkit.gcal import CalendarClient, summary_contains

import settings
from services import config_service

log = logging.getLogger(__name__)

CAKE   = "\U0001F382"            # 🎂
FLAG   = "\U0001F1EE\U0001F1F1"  # 🇮🇱
COUPLE = "\U0001f46b"            # 👫
EVENT  = "\U0001F4CC"            # 📌

EMOJI_BY_TYPE = {
    "wedding anniversary": COUPLE,
    "event": EVENT,
}

# Window used when searching the calendar for existing events.
_SEARCH_FROM = datetime(settings.CALENDAR_FIRST_YEAR, 1, 1, 0)
_SEARCH_TO   = datetime(settings.CALENDAR_LAST_YEAR, 12, 31, 23)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def _make_client() -> CalendarClient:
    return CalendarClient(
        settings.GOOGLE_CREDENTIALS_FILE,
        settings.GOOGLE_TOKEN_FILE,
        timezone=settings.CALENDAR_TIMEZONE,
        allow_browser_flow=settings.GOOGLE_ALLOW_BROWSER_AUTH,
    )


_client: Optional[CalendarClient] = None


def client() -> CalendarClient:
    """The shared, lazily-authenticated calendar client."""
    global _client
    if _client is None:
        _client = _make_client()
    return _client


def _require_calendar_id(calendar: str) -> str:
    calendar_id = config_service.get_calendar_id(calendar)
    if not calendar_id:
        raise RuntimeError(f"No calendar configured for '{calendar}'.")
    return calendar_id


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

def get_color_for_entry(entry: dict) -> Optional[str]:
    """
    Resolve the event colorId for an entry:
      1. an explicit per-entry `color` override always wins
      2. `private` calendar entries use their calendar's flat colour, type ignored
      3. otherwise the `type_colors` colour for the entry's type, or None so the
         event inherits the calendar's own colour.
    """
    if entry.get("color"):
        return entry["color"]

    calendar = (entry.get("calendar") or "").lower()
    if calendar == "private":
        return config_service.get_color(calendar, default=None)

    return config_service.get_type_color(entry.get("type", ""))


def set_calendar_display_color(calendar: str, background_hex: str, foreground_hex: str = "#000000") -> None:
    """Set a calendar's own display colour (the sidebar swatch in Google Calendar)."""
    client().set_calendar_color(_require_calendar_id(calendar), background_hex, foreground_hex)


# ---------------------------------------------------------------------------
# Writing events
# ---------------------------------------------------------------------------

def _create(calendar_id: str, day: date, summary: str, color: Optional[str]) -> bool:
    try:
        client().create_all_day_event(calendar_id, day, summary, color_id=color)
        return True
    except Exception as exc:
        log.warning("Could not create '%s' on %s: %s", summary, day, exc)
        return False


def write_english_events(calendar_id: str, name: str, born: date, color: Optional[str] = None,
                         entry_type: Optional[str] = None) -> int:
    """Yearly Gregorian events from max(first year, birth year) to the last year."""
    emoji = EMOJI_BY_TYPE.get(entry_type, CAKE)
    count = 0
    for year in range(max(settings.CALENDAR_FIRST_YEAR, born.year), settings.CALENDAR_LAST_YEAR + 1):
        try:
            day = born.replace(year=year)
        except ValueError:          # 29 Feb in a non-leap year: no event that year
            continue
        count += _create(calendar_id, day, f"{emoji} {name} ({year - born.year})", color)
    return count


def write_hebrew_events(calendar_id: str, name: str, born: date, after_shkia: bool,
                        color: Optional[str] = None, entry_type: Optional[str] = None) -> int:
    """Yearly Hebrew-calendar events (after-shkia births count from the next day)."""
    emoji = EMOJI_BY_TYPE.get(entry_type, CAKE)
    original = hebrew.to_hebrew(born, after_shkia)

    first = max(hebrew.hebrew_year_of(date(settings.CALENDAR_FIRST_YEAR, 1, 1)), original.year)
    last  = hebrew.hebrew_year_of(date(settings.CALENDAR_LAST_YEAR, 12, 31))

    count = 0
    for year in range(first, last + 1):
        h = hebrew.anniversary_in_year(original, year)
        if h is None:               # e.g. 30 Cheshvan in a short year
            continue
        count += _create(calendar_id, h.to_pydate(),
                         f"{emoji} {name} ({year - original.year}) {FLAG}", color)
    return count


def push_entry_to_calendar(entry: dict) -> dict:
    """Write English and Hebrew events for one entry. Returns {"english": n, "hebrew": n}."""
    calendar_id = _require_calendar_id(entry.get("calendar", ""))
    color = get_color_for_entry(entry)
    born  = datetime.strptime(entry["date"], "%Y-%m-%d").date()
    after_shkia = bool(entry.get("afterShkia", False))
    name  = entry["name"]
    kind  = entry.get("type")

    return {
        "english": write_english_events(calendar_id, name, born, color, kind),
        "hebrew":  write_hebrew_events(calendar_id, name, born, after_shkia, color, kind),
    }


def push_all_entries_to_calendar(entries: list) -> dict:
    """Push every entry to its own calendar. Returns {"success": n, "errors": [...]}."""
    success = 0
    errors  = []
    for entry in entries:
        try:
            push_entry_to_calendar(entry)
            success += 1
        except Exception as exc:
            errors.append({"name": entry.get("name"), "error": str(exc)})
    return {"success": success, "errors": errors}


# ---------------------------------------------------------------------------
# Removing events
# ---------------------------------------------------------------------------

def remove_entry_from_calendar(calendar: str, name: str) -> int:
    """Delete every event whose title contains *name* (case-insensitive)."""
    return client().delete_events(_require_calendar_id(calendar), _SEARCH_FROM, _SEARCH_TO,
                                  where=summary_contains(name, case_sensitive=False))


def clear_family_calendar(calendar: str) -> int:
    """Delete every event in the family's calendar. Returns count deleted."""
    return client().delete_events(_require_calendar_id(calendar), _SEARCH_FROM, _SEARCH_TO)
