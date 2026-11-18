#!/usr/bin/env python3
"""
BDays – local web application entry point.

Run with:
    python app.py

Then open http://127.0.0.1:5000 in your browser (host/port come from .env).
"""

import logging

from flask import Flask, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

import settings  # first: explains a missing CalendarKit package
from calendarkit.gcal import calendar_view_url
from services import config_service
from routes.entries        import entries_bp
from routes.families       import families_bp
from routes.calendar_routes import calendar_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Behind the login gateway (dashboard/gateway/gateway.py) the app lives under a path
    # prefix such as /bdays; X-Forwarded-Prefix makes url_for() include it.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=0, x_host=0, x_port=0, x_prefix=1)

    app.secret_key = settings.SECRET_KEY

    # Register blueprints
    app.register_blueprint(families_bp)
    app.register_blueprint(entries_bp)
    app.register_blueprint(calendar_bp)

    @app.context_processor
    def calendar_links():
        def calendar_url(family: str):
            """Browser link to a family's Google calendar, or None if not configured."""
            cal_id = config_service.get_calendar_id(family)
            return calendar_view_url(cal_id, timezone=settings.CALENDAR_TIMEZONE) if cal_id else None
        return {"calendar_url": calendar_url}

    @app.route("/")
    def root():
        return redirect(url_for("families.index"))

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    application = create_app()
    application.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
