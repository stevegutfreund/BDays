"""BDays runtime settings, read once from the environment / .env file.

Machine-specific and secret values live in ``.env`` (git-ignored; see
``.env.example``). The calendar mapping itself (family -> Google calendar id,
colours) is edited from the Settings page and stored in ``config.json``
(also git-ignored; see ``config.example.json``).
"""

import secrets
from pathlib import Path

try:
    from calendarkit import env
except ImportError as exc:  # the shared package is a separate repo
    raise SystemExit(
        "BDays needs the shared CalendarKit package. Clone the CalendarKit repo next to this "
        "folder (so that ../CalendarKit exists), then run: pip install -r requirements.txt "
        f"({exc})"
    ) from exc

BASE_DIR = Path(__file__).resolve().parent
env.load_dotenv(BASE_DIR / ".env")

# -- web server ---------------------------------------------------------------
HOST = env.get("HOST", "127.0.0.1")
PORT = env.get_int("PORT", 5000)
DEBUG = env.get_bool("FLASK_DEBUG", False)
# Without a fixed key, flash messages/sessions reset whenever the app restarts.
SECRET_KEY = env.get("SECRET_KEY") or env.get("BDAYS_SECRET_KEY") or secrets.token_hex(32)

# -- storage ------------------------------------------------------------------
DATA_DIR = env.get_path("DATA_DIR", "data", base_dir=BASE_DIR)
CONFIG_FILE = env.get_path("CONFIG_FILE", "config.json", base_dir=BASE_DIR)

# -- Google Calendar ----------------------------------------------------------
GOOGLE_CREDENTIALS_FILE = env.get_path("GOOGLE_CREDENTIALS_FILE", "credentials.json", base_dir=BASE_DIR)
GOOGLE_TOKEN_FILE = env.get_path("GOOGLE_TOKEN_FILE", "token.json", base_dir=BASE_DIR)
GOOGLE_ALLOW_BROWSER_AUTH = env.get_bool("GOOGLE_ALLOW_BROWSER_AUTH", True)
CALENDAR_TIMEZONE = env.get("CALENDAR_TIMEZONE", "Asia/Jerusalem")

# Range of years written to the calendar for recurring birthdays/anniversaries.
CALENDAR_FIRST_YEAR = env.get_int("CALENDAR_FIRST_YEAR", 2000)
CALENDAR_LAST_YEAR = env.get_int("CALENDAR_LAST_YEAR", 2100)
