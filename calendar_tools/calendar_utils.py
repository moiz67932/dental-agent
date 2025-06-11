"""Google-Calendar wrapper used by the booking tool."""
import os, datetime as dt, pytz
from dotenv import load_dotenv
from dateutil.parser import isoparse
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS = service_account.Credentials.from_service_account_file(
    os.getenv("GCAL_CREDS"), scopes=SCOPES
)
CAL_ID = os.getenv("GCAL_ID")
TZ = pytz.timezone(os.getenv("TZ", "America/Chicago"))
OPEN_START, OPEN_END = [
    dt.time.fromisoformat(t) for t in os.getenv("OPEN_HOURS", "09:00-17:00").split("-")
]
SLOT_MIN = int(os.getenv("SLOT_MINUTES", 30))

svc = build("calendar", "v3", credentials=CREDS, cache_discovery=False)


def _busy(start: dt.datetime, end: dt.datetime):
    iso = lambda d: d.astimezone(pytz.utc).isoformat()
    resp = svc.freebusy().query(
        body={"timeMin": iso(start), "timeMax": iso(end), "items": [{"id": CAL_ID}]}
    ).execute()
    return [
        (isoparse(b["start"]).astimezone(TZ), isoparse(b["end"]).astimezone(TZ))
        for b in resp["calendars"][CAL_ID]["busy"]
    ]


def free_slots(day: dt.date):
    start = TZ.localize(dt.datetime.combine(day, OPEN_START))
    end = TZ.localize(dt.datetime.combine(day, OPEN_END))
    busy = _busy(start, end)

    ptr, slots = start, []
    while ptr + dt.timedelta(minutes=SLOT_MIN) <= end:
        clash = any(b[0] < ptr + dt.timedelta(minutes=SLOT_MIN) and ptr < b[1] for b in busy)
        if not clash:
            slots.append(ptr)
        ptr += dt.timedelta(minutes=SLOT_MIN)
    return slots


def _ensure_tz(dt_obj: dt.datetime) -> dt.datetime:
    return dt_obj if dt_obj.tzinfo else TZ.localize(dt_obj)


def book(slot: str, patient: str, notes="Booked by AI"):
    start_dt = _ensure_tz(isoparse(slot))
    end_dt = start_dt + dt.timedelta(minutes=SLOT_MIN)
    body = {
        "summary": f"🦷 {patient}",
        "description": notes,
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()},
    }
    ev = svc.events().insert(calendarId=CAL_ID, body=body).execute()
    return ev.get("htmlLink")
