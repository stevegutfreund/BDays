#!/usr/bin/env python3
"""
Routes for listing, adding, editing, and deleting birthday entries.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import storage, upcoming

entries_bp = Blueprint("entries", __name__)


def _enrich(entry: dict) -> dict:
    """Add display-friendly fields to an entry dict."""
    return upcoming.enrich(entry)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@entries_bp.route("/family/<family>")
def list_entries(family: str):
    entries = [_enrich(e) for e in storage.list_entries(family)]
    return render_template(
        "entries/list.html",
        family=family,
        entries=entries,
        stats=upcoming.stats(entries),
        soon=upcoming.upcoming(entries, within_days=30, limit=6),
    )


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

def _after_shkia(form):
    """The form's before/after-shkia choice: True, False, or None if missing."""
    return {"1": True, "0": False}.get(form.get("afterShkia", "").strip())


@entries_bp.route("/family/<family>/add", methods=["GET", "POST"])
def add_entry(family: str):
    if request.method == "POST":
        name       = request.form.get("name", "").strip()
        date       = request.form.get("date", "").strip()
        after_shkia = _after_shkia(request.form)
        entry_type = request.form.get("type", "").strip()
        color      = request.form.get("color", "").strip()

        error = storage.validate_entry(name, date, after_shkia, entry_type)
        if error:
            flash(error, "error")
            return render_template("entries/form.html", family=family,
                                   action="add", entry=request.form)

        try:
            storage.add_entry(family, name, date, after_shkia, entry_type, color or None)
            flash(f"Added {name} successfully.", "success")
            return redirect(url_for("entries.list_entries", family=family))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("entries/form.html", family=family,
                                   action="add", entry=request.form)

    return render_template("entries/form.html", family=family, action="add", entry={})


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

@entries_bp.route("/family/<family>/edit/<path:name>", methods=["GET", "POST"])
def edit_entry(family: str, name: str):
    if request.method == "POST":
        new_name       = request.form.get("name", "").strip()
        new_date       = request.form.get("date", "").strip()
        new_after_shkia = _after_shkia(request.form)
        new_type       = request.form.get("type", "").strip()
        new_color      = request.form.get("color", "").strip()

        error = storage.validate_entry(new_name, new_date, new_after_shkia, new_type)
        if error:
            flash(error, "error")
            return render_template("entries/form.html", family=family,
                                   action="edit", original_name=name, entry=request.form)

        try:
            storage.update_entry(family, name, new_name, new_date, new_after_shkia,
                                  new_type, new_color or None)
            flash(f"Updated entry successfully.", "success")
            return redirect(url_for("entries.list_entries", family=family))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("entries/form.html", family=family,
                                   action="edit", original_name=name, entry=request.form)

    entry = storage.get_entry(family, name)
    if entry is None:
        flash(f"Entry '{name}' not found.", "error")
        return redirect(url_for("entries.list_entries", family=family))

    return render_template("entries/form.html", family=family,
                           action="edit", original_name=name, entry=entry)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@entries_bp.route("/family/<family>/delete/<path:name>", methods=["POST"])
def delete_entry(family: str, name: str):
    deleted = storage.delete_entry(family, name)
    if deleted:
        flash(f"Deleted '{name}'.", "success")
    else:
        flash(f"Entry '{name}' not found.", "error")
    return redirect(url_for("entries.list_entries", family=family))
