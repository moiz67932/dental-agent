# """Google-Calendar wrapper used by the booking tool."""
# import os, datetime as dt, pytz
# from dotenv import load_dotenv
# from dateutil.parser import isoparse
# from google.oauth2 import service_account
# from googleapiclient.discovery import build

# load_dotenv()

# SCOPES = ["https://www.googleapis.com/auth/calendar"]
# CREDS = service_account.Credentials.from_service_account_file(
#     os.getenv("GCAL_CREDS"), scopes=SCOPES
# )
# CAL_ID = os.getenv("GCAL_ID")

# # ── Clinic (destination) time-zone ──────────────────────────────
# TZ = pytz.timezone(os.getenv("TZ", "Asia/Karachi"))
# CUR_YEAR = dt.datetime.now(TZ).year          # ← always 2025 “today”
# OPEN_START, OPEN_END = [
#     dt.time.fromisoformat(t) for t in os.getenv("OPEN_HOURS", "09:00-17:00").split("-")
# ]
# SLOT_MIN = int(os.getenv("SLOT_MINUTES", 30))

# svc = build("calendar", "v3", credentials=CREDS, cache_discovery=False)


# def _busy(start: dt.datetime, end: dt.datetime):
#     iso = lambda d: d.astimezone(pytz.utc).isoformat()
#     resp = svc.freebusy().query(
#         body={"timeMin": iso(start), "timeMax": iso(end), "items": [{"id": CAL_ID}]}
#     ).execute()
#     return [
#         (isoparse(b["start"]).astimezone(TZ), isoparse(b["end"]).astimezone(TZ))
#         for b in resp["calendars"][CAL_ID]["busy"]
#     ]


# def free_slots(day: dt.date):
#     start = TZ.localize(dt.datetime.combine(day, OPEN_START))
#     end = TZ.localize(dt.datetime.combine(day, OPEN_END))
#     busy = _busy(start, end)

#     ptr, slots = start, []
#     while ptr + dt.timedelta(minutes=SLOT_MIN) <= end:
#         clash = any(b[0] < ptr + dt.timedelta(minutes=SLOT_MIN) and ptr < b[1] for b in busy)
#         if not clash:
#             slots.append(ptr)
#         ptr += dt.timedelta(minutes=SLOT_MIN)
#     return slots


# # ────────────────── helpers ─────────────────────────────────────

# def _coerce_year(dt_obj: dt.datetime) -> dt.datetime:
#     """
#     If the parsed date came in with a placeholder/older year (often 1900
#     when the LLM omits it), bump it to the *current clinic year* (2025).
#     """
#     if dt_obj.year < CUR_YEAR:          # treat anything pre-2025 as “missing”
#         try:
#             dt_obj = dt_obj.replace(year=CUR_YEAR)
#         except ValueError:
#             # Handle 29 Feb → 28 Feb when current year is non-leap
#             dt_obj = dt_obj.replace(month=2, day=28, year=CUR_YEAR)
#     return dt_obj


# def _ensure_tz(dt_obj: dt.datetime) -> dt.datetime:
#     """
#     Attach the clinic time-zone if missing **and** coerce the year to 2025.
#     """
#     dt_obj = _coerce_year(dt_obj)
#     return dt_obj if dt_obj.tzinfo else TZ.localize(dt_obj)


# # ────────────────── public API ──────────────────────────────────

# def book(slot: str, patient: str, notes: str = "Booked by AI"):
#     """
#     Create a calendar event at `slot` — ISO-8601 (caller or clinic TZ).
#     Ensures TZ is set and year == 2025 before pushing to Google Calendar.
#     """
#     start_dt = _ensure_tz(isoparse(slot))
#     end_dt = start_dt + dt.timedelta(minutes=SLOT_MIN)
#     body = {
#         "summary": f"🦷 {patient}",
#         "description": notes,
#         "start": {"dateTime": start_dt.isoformat()},
#         "end": {"dateTime": end_dt.isoformat()},
#     }
#     ev = svc.events().insert(calendarId=CAL_ID, body=body).execute()
#     return ev.get("htmlLink")






"""
calendar_utils.py – Google-Calendar wrapper
• Always coerces the date into the CURRENT clinic year (2025).
• Variable slot lengths still supported.
"""
import os, datetime as dt, pytz
from dotenv import load_dotenv
from dateutil.parser import isoparse
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS  = service_account.Credentials.from_service_account_file(
    os.getenv("GCAL_CREDS"), scopes=SCOPES
)
CAL_ID = os.getenv("GCAL_ID")

TZ        = pytz.timezone(os.getenv("TZ", "Asia/Karachi"))
CUR_YEAR  = dt.datetime.now(TZ).year          # 2025
OPEN_START, OPEN_END = [
    dt.time.fromisoformat(t) for t in os.getenv("OPEN_HOURS","09:00-17:00").split("-")
]

svc = build("calendar", "v3", credentials=CREDS, cache_discovery=False)

# ───────────────── helpers ──────────────────
def _ensure_year(d: dt.datetime) -> dt.datetime:
    """
    Replace the year with the clinic's current year if it's different.
    Handles leap-day edge (29 Feb → 28 Feb on non-leap).
    """
    if d.year != CUR_YEAR:
        try:
            d = d.replace(year=CUR_YEAR)
        except ValueError:          # 29-Feb on non-leap
            d = d.replace(month=2, day=28, year=CUR_YEAR)
    return d

def _ensure_tz(d: dt.datetime) -> dt.datetime:
    """
    1. Force correct year, 2. Attach clinic TZ if missing.
    """
    d = _ensure_year(d)
    return d if d.tzinfo else TZ.localize(d)

def _busy(day_start: dt.datetime, day_end: dt.datetime):
    iso = lambda x: x.astimezone(pytz.utc).isoformat()
    resp = svc.freebusy().query(
        body={"timeMin": iso(day_start), "timeMax": iso(day_end), "items":[{"id":CAL_ID}]}
    ).execute()
    return [
        (isoparse(b["start"]).astimezone(TZ), isoparse(b["end"]).astimezone(TZ))
        for b in resp["calendars"][CAL_ID]["busy"]
    ]

def free_slots(day: dt.date, duration_min: int):
    start = TZ.localize(dt.datetime.combine(day, OPEN_START))
    end   = TZ.localize(dt.datetime.combine(day, OPEN_END))
    busy  = _busy(start, end)

    delta = dt.timedelta(minutes=duration_min)
    ptr, slots = start, []
    while ptr + delta <= end:
        clash = any(b[0] < ptr + delta and ptr < b[1] for b in busy)
        if not clash:
            slots.append(ptr)
        ptr += dt.timedelta(minutes=15)
    return slots

def book(slot_iso: str, patient: str, notes: str, duration_min: int):
    start_dt = _ensure_tz(isoparse(slot_iso))
    end_dt   = start_dt + dt.timedelta(minutes=duration_min)
    ev = svc.events().insert(
        calendarId=CAL_ID,
        body={
            "summary": f"🦷 {patient}",
            "description": notes,
            "start": {"dateTime": start_dt.isoformat()},
            "end":   {"dateTime": end_dt.isoformat()},
        },
    ).execute()
    return ev.get("htmlLink")
