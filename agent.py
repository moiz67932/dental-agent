# import os
# import logging
# import datetime as dt
# import re
# from typing import List

# from dotenv import load_dotenv

# from livekit.agents import (
#     Agent, AgentSession, AutoSubscribe,
#     JobContext, JobProcess, WorkerOptions, cli, metrics,
#     RoomInputOptions, function_tool, RunContext,
# )
# from livekit.plugins import deepgram, noise_cancellation, silero, cartesia
# from livekit.plugins.openai import LLM  # still used for general assistant replies – **not** for digits

# from prompts import DENTAL_RECEPTIONIST_PROMPT
# from rag.vector_store import search
# from calendar_tools.calendar_utils import book, free_slots, TZ
# from whatsapp_sender import send_wa  # <- make sure this helper uses (to, body)

# # ---------------------------------------------------------------------------
# # Init & logging
# # ---------------------------------------------------------------------------
# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("voice-agent")

# # ---------------------------------------------------------------------------
# # RAG helper (unchanged)
# # ---------------------------------------------------------------------------

# def enrich(txt: str, k: int = 3) -> str:
#     hits = search(txt, k=k)
#     if not hits:
#         return txt
#     refs = "\n".join(f"{r[0]}: {r[1]} (Price {r[2]})" for r in hits if len(r) >= 3)
#     return f"{txt}\n\n[Reference docs]\n{refs}\n"

# # ---------------------------------------------------------------------------
# # PHONE‑NUMBER UTILITIES  📴  (robust heuristics, **no external LLM calls**)
# # ---------------------------------------------------------------------------

# WORD2DIGIT = {
#     "zero": "0", "oh": "0", "o": "0",
#     "one": "1", "two": "2", "three": "3", "four": "4",
#     "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
#     "plus": "+", "double": "x2",  # handled later
# }
# RE_DIGIT = re.compile(r"\d")


# def normalise_phone_fragment(fragment: str) -> str:
#     """Convert a transcript fragment → clean digit string.
#     Returns "" (empty string) when no digits detected – avoids noisy errors."""
#     fragment = fragment.lower()

#     # 1. "double three" → "three three"
#     fragment = re.sub(r"double\s+(\w+)", lambda m: f"{m.group(1)} {m.group(1)}", fragment)

#     tokens: List[str] = []
#     for tok in fragment.split():
#         if tok.isdigit():
#             tokens.append(tok)
#         elif tok in WORD2DIGIT and WORD2DIGIT[tok] != "x2":
#             tokens.append(WORD2DIGIT[tok])
#         elif tok.startswith("+") and tok[1:].isdigit():
#             tokens.append(tok)
#         else:
#             if RE_DIGIT.search(tok):
#                 digits_only = re.sub(r"\D", "", tok)
#                 tokens.append(digits_only)

#     raw = "".join(tokens)
#     return raw  # may be "" when nothing useful found

# # ---------------------------------------------------------------------------
# # TOOL: collect_phone_fragment
# # ---------------------------------------------------------------------------

# @function_tool(name="collect_phone_fragment")
# async def collect_phone_fragment(context: RunContext, fragment: str):
#     """Collect phone fragments into session._userdata['patient_data']."""
#     session: AgentSession = context.session

#     # Safe persistent dict on the session (works with current LiveKit build)
#     if not hasattr(session, "_userdata") or session._userdata is None:
#         session._userdata = {}
#     pdata = session._userdata.setdefault("patient_data", {})

#     buf: str = pdata.get("phone_buf", "")
#     new_part = normalise_phone_fragment(fragment)

#     if not new_part:
#         # no digits detected; ignore gracefully
#         return "Got it – please continue with the next digits."

#     if not buf.endswith(new_part):
#         buf += new_part
#         buf = buf[-15:]  # keep max 15 chars
#         pdata["phone_buf"] = buf

#     num_digits = re.sub(r"\D", "", buf)
#     if 10 <= len(num_digits) <= 15:
#         phone = "+" + num_digits if not buf.startswith("+") else buf
#         pdata["phone"] = phone
#         pdata["phone_valid"] = True
#         logger.info("✅ Phone captured: %s", phone)
#         return f"Thanks! I’ve captured your number as {phone}."

#     logger.info("…phone fragment queued: %s -> buf=%s", fragment, buf)
#     return "Got it – could you give me the remaining digits?"

# # ---------------------------------------------------------------------------
# # TOOL: schedule_appointment
# # ---------------------------------------------------------------------------

# @function_tool(
#     name="schedule_appointment",
#     description="Book a 30‑minute consult once patient, phone & time are confirmed."
# )
# async def schedule_appointment(
#     context: RunContext,
#     patient: str,
#     iso_start: str,
#     chief_concern: str | None = None,
# ):
#     if iso_start.endswith("Z"):
#         iso_start = iso_start.replace("Z", "+00:00")
#     try:
#         start_dt = dt.datetime.fromisoformat(iso_start)
#     except ValueError:
#         return "⛔ That date/time didn’t parse – could you rephrase?"

#     if not start_dt.tzinfo:
#         start_dt = TZ.localize(start_dt)
#     else:
#         start_dt = start_dt.astimezone(TZ)

#     duration = int(os.getenv("SLOT_MINUTES", "30"))
#     match = next(
#         (s for s in free_slots(start_dt.date(), duration)
#          if abs((s - start_dt).total_seconds()) < 60),
#         None,
#     )
#     if not match:
#         return "⛔ That slot is busy – let’s pick another time."

#     link = book(match.isoformat(), patient, chief_concern or "Consult", duration)
#     hour_fmt = match.strftime("%I:%M %p").lstrip("0")

#     # WhatsApp – simple text body
#     phone = None
#     if hasattr(context.session, "_userdata") and context.session._userdata:
#         phone = context.session._userdata.get("patient_data", {}).get("phone")
#     if phone:
#         logger.info("📤 WA → %s", phone)
#         try:
#             send_wa(
#                 to=phone,
#                 body=(
#                     f"Hi {patient}, your {chief_concern or 'appointment'} is confirmed for "
#                     f"{match.strftime('%d %b %Y')} at {hour_fmt}. See you then!"
#                 ),
#             )
#         except Exception as e:
#             logger.error("❌ WhatsApp send fail: %s", e)

#     context.session.say(
#         f"Great, {patient}! You’re confirmed for {match.strftime('%A')} at {hour_fmt}. "
#         "You’ll receive a confirmation shortly."
#     )
#     return f"✅ Booked! {link}"

# # ---------------------------------------------------------------------------
# # Assistant & entry‑point (unchanged logic)
# # ---------------------------------------------------------------------------

# class Assistant(Agent):
#     def __init__(self):
#         super().__init__(
#             instructions=DENTAL_RECEPTIONIST_PROMPT,
#             stt=deepgram.STT(),
#             llm=LLM(model="gpt-4.1-nano-2025-04-14"),
#             tts=cartesia.TTS(),
#             tools=[collect_phone_fragment, schedule_appointment],
#         )

#     async def on_enter(self):
#         try:
#             self.session.say("Hi, Arlington Dental Clinic—how can I help you?")
#         except RuntimeError:
#             pass


# def prewarm(proc: JobProcess):
#     proc.userdata["vad"] = silero.VAD.load()


# def safe_text_input(session: AgentSession, txt: str):
#     try:
#         return session.generate_reply(user_input=enrich(txt))
#     except RuntimeError:
#         return None


# async def entrypoint(ctx: JobContext):
#     logger.info("Connecting to room %s", ctx.room.name)
#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

#     participant = await ctx.wait_for_participant()
#     logger.info("Assistant started for %s", participant.identity)

#     usage = metrics.UsageCollector()
#     session = AgentSession(
#         vad=ctx.proc.userdata["vad"],
#         min_endpointing_delay=0.5,
#         max_endpointing_delay=5.0,
#     )
#     session.on("metrics_collected", lambda m: (metrics.log_metrics(m), usage.collect(m)))

#     def on_final(ev):
#         if ev.is_final:
#             session.generate_reply(user_input=enrich(ev.transcript))

#     session.on("user_input_transcribed", on_final)

#     await session.start(
#         room=ctx.room,
#         agent=Assistant(),
#         room_input_options=RoomInputOptions(
#             noise_cancellation=noise_cancellation.BVC(),
#             text_input_cb=safe_text_input,
#         ),
#     )


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))










import os
import logging
import datetime as dt
import re
from typing import List, Optional

from dotenv import load_dotenv

from livekit.agents import (
    Agent, AgentSession, AutoSubscribe,
    JobContext, JobProcess, WorkerOptions, cli, metrics,
    RoomInputOptions, function_tool, RunContext,
)
from livekit.plugins import deepgram, noise_cancellation, silero, cartesia
from livekit.plugins.openai import LLM  # still used for conversational replies – **not** for digit extraction

from prompts import DENTAL_RECEPTIONIST_PROMPT
from rag import vector_store  # reuse its embed() + connection settings
from calendar_tools.calendar_utils import book, free_slots, TZ
from whatsapp_sender import send_wa  # helper must support kwargs to, body

import psycopg2  # direct duration lookup

# ---------------------------------------------------------------------------
# Init & logging
# ---------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# PostgreSQL connection params (same as vector_store)
PG_DSN = dict(
    dbname=os.getenv("PG_DB"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASS"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT"),
)

# ---------------------------------------------------------------------------
# RAG helper (unchanged)
# ---------------------------------------------------------------------------

def enrich(txt: str, k: int = 3) -> str:
    hits = vector_store.search(txt, k=k)
    if not hits:
        return txt
    refs = "\n".join(f"{r[0]}: {r[1]} (Price {r[2]})" for r in hits if len(r) >= 3)
    return f"{txt}\n\n[Reference docs]\n{refs}\n"

# ---------------------------------------------------------------------------
# PHONE‑NUMBER UTILITIES  📴  (robust heuristics, **no external LLM calls**)
# ---------------------------------------------------------------------------

WORD2DIGIT = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "plus": "+", "double": "x2",  # handled later
}
RE_DIGIT = re.compile(r"\d")


def normalise_phone_fragment(fragment: str) -> str:
    """Convert a transcript fragment → clean digit string.
    Returns "" (empty string) when no digits detected – avoids noisy errors."""
    fragment = fragment.lower()

    # 1. "double three" → "three three"
    fragment = re.sub(r"double\s+(\w+)", lambda m: f"{m.group(1)} {m.group(1)}", fragment)

    tokens: List[str] = []
    for tok in fragment.split():
        if tok.isdigit():
            tokens.append(tok)
        elif tok in WORD2DIGIT and WORD2DIGIT[tok] != "x2":
            tokens.append(WORD2DIGIT[tok])
        elif tok.startswith("+") and tok[1:].isdigit():
            tokens.append(tok)
        else:
            if RE_DIGIT.search(tok):
                digits_only = re.sub(r"\D", "", tok)
                tokens.append(digits_only)

    raw = "".join(tokens)
    return raw  # may be "" when nothing useful found

# ---------------------------------------------------------------------------
# TOOL: collect_phone_fragment
# ---------------------------------------------------------------------------

@function_tool(name="collect_phone_fragment")
async def collect_phone_fragment(context: RunContext, fragment: str):
    """Collect phone fragments into session._userdata['patient_data']."""
    session: AgentSession = context.session

    # Safe persistent dict on the session (works with current LiveKit build)
    if not hasattr(session, "_userdata") or session._userdata is None:
        session._userdata = {}
    pdata = session._userdata.setdefault("patient_data", {})

    buf: str = pdata.get("phone_buf", "")
    new_part = normalise_phone_fragment(fragment)

    if not new_part:
        return "Got it – please continue with the next digits."

    if not buf.endswith(new_part):
        buf += new_part
        buf = buf[-15:]  # keep max 15 chars
        pdata["phone_buf"] = buf

    num_digits = re.sub(r"\D", "", buf)
    if 10 <= len(num_digits) <= 15:
        phone = "+" + num_digits if not buf.startswith("+") else buf
        pdata["phone"] = phone
        pdata["phone_valid"] = True
        logger.info("✅ Phone captured: %s", phone)
        return f"Thanks! I’ve captured your number as {phone}."

    logger.info("…phone fragment queued: %s -> buf=%s", fragment, buf)
    return "Got it – could you give me the remaining digits?"

# ---------------------------------------------------------------------------
# APPOINTMENT‑DURATION LOGIC  ⏱️  (now sourced from RAG DB)
# ---------------------------------------------------------------------------

DEFAULT_DURATION = int(os.getenv("SLOT_MINUTES", "30"))  # fallback
ROUND_TO = 30  # block size sent to Google Cal

DURATION_RE = re.compile(r"(\d+)(?:\s*(?:mins?|minutes?|m))?", re.I)
HOUR_RE = re.compile(r"(\d+)\s*hour", re.I)


def _parse_duration_field(text: str) -> Optional[int]:
    """Convert a CSV duration cell → minutes.
    Handles '45–60 minutes', '2 visits (60 min each)', '90 minutes', 'Varies'."""
    if not text:
        return None
    text = text.strip()
    if text.lower().startswith("varies"):
        return None

    # Look for hour(s)
    m = HOUR_RE.search(text)
    if m:
        hours = int(m.group(1))
        return hours * 60

    # Look for numeric minutes – take the first number
    m = DURATION_RE.search(text)
    if m:
        return int(m.group(1))

    return None


def lookup_duration(chief: str | None) -> int:
    """Use pgvector nearest‑match to fetch Duration column."""
    if not chief:
        return DEFAULT_DURATION

    vec = vector_store.embed(chief)
    vec_literal = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

    with psycopg2.connect(**PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name, duration
                FROM dental_services
                ORDER BY embedding <-> %s::vector
                LIMIT 1
                """,
                (vec_literal,),
            )
            row = cur.fetchone()
            if row and row[1]:
                mins = _parse_duration_field(row[1])
                if mins:
                    logger.info("🕑 Duration '%s' -> %s min", row[1], mins)
                    return mins
    return DEFAULT_DURATION


def round_up(minutes: int, base: int = ROUND_TO) -> int:
    return ((minutes + base - 1) // base) * base

# ---------------------------------------------------------------------------
# TOOL: schedule_appointment
# ---------------------------------------------------------------------------

@function_tool(
    name="schedule_appointment",
    description="Book a consult once patient, phone & time are confirmed. Duration auto‑set per treatment.",
)
async def schedule_appointment(
    context: RunContext,
    patient: str,
    iso_start: str,
    chief_concern: str | None = None,
):
    if iso_start.endswith("Z"):
        iso_start = iso_start.replace("Z", "+00:00")
    try:
        start_dt = dt.datetime.fromisoformat(iso_start)
    except ValueError:
        return "⛔ That date/time didn’t parse – could you rephrase?"

    if not start_dt.tzinfo:
        start_dt = TZ.localize(start_dt)
    else:
        start_dt = start_dt.astimezone(TZ)

    raw_dur = lookup_duration(chief_concern)
    duration = round_up(raw_dur)

    # find a free slot that can accommodate the **entire** duration
    slots = free_slots(start_dt.date(), duration)
    match = next(
        (s for s in slots if abs((s - start_dt).total_seconds()) < 60),
        None,
    )
    if not match:
        return "⛔ That slot is busy – let’s pick another time (or adjust duration)."

    link = book(match.isoformat(), patient, chief_concern or "Consult", duration)
    hour_fmt = match.strftime("%I:%M %p").lstrip("0")

    # WhatsApp – simple text body
    phone = None
    if hasattr(context.session, "_userdata") and context.session._userdata:
        phone = context.session._userdata.get("patient_data", {}).get("phone")
    if phone:
        logger.info("📤 WA → %s", phone)
        try:
            send_wa(
                to=phone,
                body=(
                    f"Hi {patient}, your {chief_concern or 'appointment'} is confirmed for "
                    f"{match.strftime('%d %b %Y')} at {hour_fmt}. "
                    f"Allocated time: {duration} min. See you then!"
                ),
            )
        except Exception as e:
            logger.error("❌ WhatsApp send fail: %s", e)

    context.session.say(
        f"Great, {patient}! You’re confirmed for {match.strftime('%A')} at {hour_fmt}. "
        f"We’ve set aside {duration} minutes for you. You’ll receive a confirmation shortly."
    )
    return f"✅ Booked! {link} (duration {duration} min)"

# ---------------------------------------------------------------------------
# Assistant & entry‑point (unchanged logic)
# ---------------------------------------------------------------------------

class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=DENTAL_RECEPTIONIST_PROMPT,
            stt=deepgram.STT(),
            llm=LLM(model="gpt-4.1-nano-2025-04-14"),
            tts=cartesia.TTS(),
            tools=[collect_phone_fragment, schedule_appointment],
        )

    async def on_enter(self):
        try:
            self.session.say("Hi, Arlington Dental Clinic—how can I help you?")
        except RuntimeError:
            pass


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


def safe_text_input(session: AgentSession, txt: str):
    try:
        return session.generate_reply(user_input=enrich(txt))
    except RuntimeError:
        return None


async def entrypoint(ctx: JobContext):
    logger.info("Connecting to room %s", ctx.room.name)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info("Assistant started for %s", participant.identity)

    usage = metrics.UsageCollector()
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
    )
    session.on("metrics_collected", lambda m: (metrics.log_metrics(m), usage.collect(m)))

    def on_final(ev):
        if ev.is_final:
            session.generate_reply(user_input=enrich(ev.transcript))

    session.on("user_input_transcribed", on_final)

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            text_input_cb=safe_text_input,
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
