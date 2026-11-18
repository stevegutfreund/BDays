#!/usr/bin/env python3
"""
Routes for Google Calendar operations, actioned from the entries list page:
  - push a single entry to calendar
  - push all entries for a family
  - clear all events for a family
  - clear a single person from a family calendar
"""

from flask import Blueprint, flash, redirect, url_for

from services import storage, calendar_service

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/family/<family>/calendar/push-all", methods=["POST"])
def push_all(family: str):
    entries = storage.list_entries(family)
    try:
        result = calendar_service.push_all_entries_to_calendar(entries)
        flash(
            f"Pushed {result['success']} entries to calendar."
            + (f" {len(result['errors'])} errors." if result["errors"] else ""),
            "success" if not result["errors"] else "warning",
        )
    except Exception as exc:
        flash(f"Calendar error: {exc}", "error")
    return redirect(url_for("entries.list_entries", family=family))


@calendar_bp.route("/family/<family>/calendar/clear-all", methods=["POST"])
def clear_all(family: str):
    try:
        count = calendar_service.clear_family_calendar(family)
        flash(f"Cleared {count} events from the calendar.", "success")
    except Exception as exc:
        flash(f"Calendar error: {exc}", "error")
    return redirect(url_for("entries.list_entries", family=family))


@calendar_bp.route("/family/<family>/calendar/push/<path:name>", methods=["POST"])
def push_entry(family: str, name: str):
    entry = storage.get_entry(family, name)
    if entry is None:
        flash(f"Entry '{name}' not found.", "error")
        return redirect(url_for("entries.list_entries", family=family))
    try:
        result = calendar_service.push_entry_to_calendar(entry)
        flash(
            f"Created {result['english']} English and {result['hebrew']} Hebrew events for {name}.",
            "success",
        )
    except Exception as exc:
        flash(f"Calendar error: {exc}", "error")
    return redirect(url_for("entries.list_entries", family=family))


@calendar_bp.route("/family/<family>/calendar/clear/<path:name>", methods=["POST"])
def clear_entry(family: str, name: str):
    try:
        count = calendar_service.remove_entry_from_calendar(family, name)
        flash(f"Removed {count} calendar events for '{name}'.", "success")
    except Exception as exc:
        flash(f"Calendar error: {exc}", "error")
    return redirect(url_for("entries.list_entries", family=family))
