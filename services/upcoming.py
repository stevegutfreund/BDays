#!/usr/bin/env python3
"""
Display helpers for entries: formatted dates, age, and the next Gregorian and
Hebrew anniversaries (mirroring the rules calendar_service uses when it writes
events, so the "upcoming" view matches what lands in Google Calendar).
"""

from datetime import date, datetime
from typing import List, Optional

from calendarkit import hebrew


def _parse(date_str: str) -> Optional[date]:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def _next_gregorian(d: date, today: date) -> date:
    for year in (today.year, today.year + 1):
        try:
            candidate = d.replace(year=year)
        except ValueError:          # 29 Feb in a non-leap year → 28 Feb
            candidate = date(year, 2, 28)
        if candidate >= today:
            return candidate
    return candidate


def _next_hebrew(d: date, after_shkia: bool, today: date):
    """Return (gregorian_date, hebrew_years) of the next Hebrew anniversary."""
    original = hebrew.to_hebrew(d, after_shkia)
    return hebrew.next_anniversary(original, today) or (None, None)


def _initials(name: str) -> str:
    parts = [p.strip() for p in name.replace("&", " & ").split() if p.strip()]
    if "&" in parts:
        i = parts.index("&")
        left, right = parts[:i], parts[i + 1:]
        if left and right:
            return (left[0][0] + right[0][0]).upper()
    letters = [p[0] for p in parts if p[0].isalnum()]
    return "".join(letters[:2]).upper() or "?"


def _relative(days: int) -> str:
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    if days < 14:
        return f"In {days} days"
    if days < 60:
        return f"In {days // 7} weeks"
    return f"In {round(days / 30.4)} months"


def enrich(entry: dict, today: Optional[date] = None) -> dict:
    """Return a copy of *entry* with display-friendly fields added."""
    today = today or date.today()
    e = dict(entry)
    d = _parse(e.get("date", ""))
    e["initials"] = _initials(e.get("name", ""))
    e["hebrew_date"] = None

    if d is None:
        e.update(date_display=e.get("date", ""), age=None, next=None, days_until=None)
        return e

    e["hebrew_date"] = hebrew.format_hebrew(hebrew.to_hebrew(d, bool(e.get("afterShkia", False))))
    e["date_display"] = d.strftime("%d %b %Y")
    e["age"] = today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    g_next = _next_gregorian(d, today)
    h_next, h_years = _next_hebrew(d, bool(e.get("afterShkia", False)), today)

    e["next_greg"] = {
        "date": g_next.isoformat(),
        "display": g_next.strftime("%a, %d %b"),
        "days": (g_next - today).days,
        "years": g_next.year - d.year,
    }
    e["next_heb"] = None
    if h_next:
        e["next_heb"] = {
            "date": h_next.isoformat(),
            "display": h_next.strftime("%a, %d %b"),
            "days": (h_next - today).days,
            "years": h_years,
        }

    # The soonest of the two drives "upcoming" ordering.
    candidates = [("greg", e["next_greg"])] + ([("heb", e["next_heb"])] if e["next_heb"] else [])
    kind, nxt = min(candidates, key=lambda c: c[1]["days"])
    e["next"] = dict(nxt, kind=kind, relative=_relative(nxt["days"]))
    e["days_until"] = nxt["days"]
    return e


def upcoming(entries: List[dict], within_days: int = 30, limit: int = None) -> List[dict]:
    """
    One row per upcoming occurrence (Gregorian and Hebrew are separate calendar
    events) within *within_days*, soonest first. Each row is the enriched entry
    plus an ``occ`` dict describing that occurrence.
    """
    rows = []
    for e in entries:
        for kind in ("greg", "heb"):
            occ = e.get(f"next_{kind}")
            if occ and occ["days"] <= within_days:
                rows.append(dict(e, occ=dict(occ, kind=kind, relative=_relative(occ["days"]))))
    rows.sort(key=lambda r: (r["occ"]["days"], r["occ"]["kind"], r.get("name", "")))
    return rows[:limit] if limit else rows


def stats(entries: List[dict]) -> dict:
    return {
        "total": len(entries),
        "birthdays": sum(1 for e in entries if e.get("type", "birthday") == "birthday"),
        "anniversaries": sum(1 for e in entries if e.get("type") == "wedding anniversary"),
        "events": sum(1 for e in entries if e.get("type") == "event"),
        "next_30": sum(1 for e in entries if e.get("days_until") is not None and e["days_until"] <= 30),
    }
