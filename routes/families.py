#!/usr/bin/env python3
"""
Routes for family management (list, add, settings).
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import storage, config_service, upcoming

families_bp = Blueprint("families", __name__)


@families_bp.route("/")
def index():
    families = storage.list_families()
    cal_cfg  = {c["family"]: c for c in config_service.list_calendar_configs()}

    by_family, everyone = {}, []
    for f in families:
        enriched = [dict(upcoming.enrich(e), family=f) for e in storage.list_entries(f)]
        by_family[f] = {
            "stats": upcoming.stats(enriched),
            "next": (upcoming.upcoming(enriched, within_days=400, limit=1) or [None])[0],
        }
        everyone.extend(enriched)

    soon = upcoming.upcoming(everyone, within_days=30)
    return render_template("families/index.html",
                           families=families, by_family=by_family, cal_cfg=cal_cfg,
                           soon=soon, total=len(everyone))


@families_bp.route("/family/add", methods=["GET", "POST"])
def add_family():
    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        calendar_id = request.form.get("calendar_id", "").strip()
        color       = request.form.get("color", "").strip()

        if not name:
            flash("Family name cannot be empty.", "error")
            return render_template("families/add.html")

        if storage.family_exists(name):
            flash(f"Family '{name}' already exists.", "error")
            return render_template("families/add.html")

        if not calendar_id:
            flash("A Google Calendar ID is required to create a family.", "error")
            return render_template("families/add.html")

        config_service.set_calendar_mapping(name, calendar_id, color or None)
        flash(f"Family '{name.capitalize()}' created.", "success")
        return redirect(url_for("families.index"))

    return render_template("families/add.html")


@families_bp.route("/settings")
def settings():
    cal_cfg = config_service.list_calendar_configs()
    return render_template("families/settings.html", cal_cfg=cal_cfg)


@families_bp.route("/settings/update", methods=["POST"])
def update_calendar():
    family      = request.form.get("family", "").strip()
    calendar_id = request.form.get("calendar_id", "").strip()
    color       = request.form.get("color", "").strip()

    if not family or not calendar_id:
        flash("Family and Calendar ID are required.", "error")
    else:
        config_service.set_calendar_mapping(family, calendar_id, color or None)
        flash(f"Calendar mapping for '{family}' updated.", "success")

    return redirect(url_for("families.settings"))
