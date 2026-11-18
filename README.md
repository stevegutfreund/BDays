# BDays

A local birthday and anniversary manager with Google Calendar integration and
Hebrew calendar support. Every entry is written to its family's Google calendar
as yearly Gregorian **and** Hebrew-date events.

## Requirements

- Python 3.10+
- **The shared [CalendarKit](../CalendarKit) package.** It is a separate repo, so clone
  it next to this one; `requirements.txt` installs it from `../CalendarKit`:

  ```text
  some-folder/
    CalendarKit/  <- git clone .../CalendarKit
    BDays/        <- this repo
  ```
- A Google Cloud OAuth client (`credentials.json`, "Desktop app" type) with the
  Calendar API enabled – only needed for calendar sync

## Setup

```bash
pip install -r requirements.txt          # includes -e ../CalendarKit
cp .env.example .env                     # then set SECRET_KEY
cp config.example.json config.json       # or add families from the UI
python app.py
```

Open **http://127.0.0.1:5000**. The first calendar action opens a browser tab
for Google consent and saves `token.json`.

## Configuration

| File                  | Holds                                                        | In git |
| --------------------- | ------------------------------------------------------------ | ------ |
| `.env`                | port, secret key, OAuth file paths, time zone, year range    | no (`.env.example` is) |
| `config.json`         | family → Google calendar id, colours (edited at `/settings`) | no (`config.example.json` is) |
| `data/entries.json`   | the entries                                                  | no (`data/entries.sample.json` is) |
| `credentials.json`, `token.json` | Google OAuth client / user token                  | no |

All settings are read in [settings.py](settings.py).

## Data format

`data/entries.json` is one array:

```json
{ "name": "Bob & Carol", "date": "2005-07-22", "afterShkia": true,
  "type": "wedding anniversary", "calendar": "smith", "family": "smith" }
```

- **type** – `birthday`, `wedding anniversary` or `event`
- **afterShkia** – `true` if it happened *after shkia*: the Hebrew date is the next day's
- **calendar** – which configured calendar the entry is pushed to
- **color** – optional Google `colorId` override

## Usage

| URL                     | Description                                   |
| ----------------------- | --------------------------------------------- |
| `/`                     | All families + what's coming up               |
| `/family/<name>`        | Entries of a family; push/clear calendar      |
| `/family/<name>/add`    | Add an entry                                  |
| `/family/add`           | Add a family (needs a Google calendar id)     |
| `/settings`             | Edit calendar ids and colours                 |

## Project structure

```
BDays/
  app.py                  Flask entry point
  settings.py             .env-backed settings
  routes/                 entries, families, calendar_routes
  services/
    storage.py            entries.json CRUD + validation
    config_service.py     config.json (calendar mapping)
    calendar_service.py   BDays event naming/colours -> calendarkit.gcal
    upcoming.py           next Gregorian/Hebrew dates for the UI (calendarkit.hebrew)
  templates/, static/
  data/
```

Files ending in `.depr` are no longer used and will be deleted; they are git-ignored.
