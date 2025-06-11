# import logging, datetime as dt
# from dotenv import load_dotenv

# from livekit.agents import (
#     Agent, AgentSession, AutoSubscribe,
#     JobContext, JobProcess, WorkerOptions, cli, metrics,
#     RoomInputOptions, function_tool, RunContext
# )
# from livekit.plugins import deepgram, noise_cancellation, silero, cartesia
# from livekit.plugins.openai import LLM

# from prompts import DENTAL_RECEPTIONIST_PROMPT
# from rag.vector_store import search
# from calendar_tools.calendar_utils import book, free_slots, TZ

# load_dotenv()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("voice-agent")

# def enrich(txt: str, k: int = 3) -> str:
#     hits = search(txt, k=k)
#     if not hits:
#         return txt
#     refs = "\n".join(f"{n}: {d} (Price {p})" for n, d, p in hits)
#     return f"{txt}\n\n[Reference docs]\n{refs}\n"

# @function_tool(
#     name="schedule_appointment",
#     description="Book a 30-minute consultation slot once the patient name and ISO start time are agreed."
# )
# async def schedule_appointment(
#     context: RunContext,
#     patient: str,
#     iso_start: str,
#     notes: str | None = None,
# ) -> str:
#     start_dt = dt.datetime.fromisoformat(iso_start)
#     if not start_dt.tzinfo:
#         start_dt = TZ.localize(start_dt)
#     else:
#         start_dt = start_dt.astimezone(TZ)

#     slots = free_slots(start_dt.date())

#     match = next((s for s in slots if abs((s - start_dt).total_seconds()) < 60), None)
#     if not match:
#         return "⛔ That slot is unavailable or outside clinic hours."

#     link = book(match.isoformat(), patient, notes or "Booked by AI receptionist")
#     hour_fmt = match.strftime("%I:%M %p").lstrip("0")
#     context.session.say(
#         f"Great, {patient}! You’re confirmed for {match.strftime('%A')} at {hour_fmt}. You’ll receive a confirmation shortly."
#     )
#     return f"Booked at {match.isoformat()}. Link: {link}"

# class Assistant(Agent):
#     def __init__(self):
#         super().__init__(
#             instructions=DENTAL_RECEPTIONIST_PROMPT,
#             stt=deepgram.STT(),
#             llm=LLM(model="gpt-4.1-nano-2025-04-14"),
#             tts=cartesia.TTS(),
#             tools=[schedule_appointment],
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







import logging, datetime as dt
from dotenv import load_dotenv

from livekit.agents import (
    Agent, AgentSession, AutoSubscribe,
    JobContext, JobProcess, WorkerOptions, cli, metrics,
    RoomInputOptions, function_tool, RunContext
)
from livekit.plugins import deepgram, noise_cancellation, silero, cartesia
from livekit.plugins.openai import LLM

from prompts import DENTAL_RECEPTIONIST_PROMPT
from rag.vector_store import search
from calendar_tools.calendar_utils import book, free_slots, TZ

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

def enrich(txt: str, k: int = 3) -> str:
    hits = search(txt, k=k)
    if not hits:
        return txt
    refs = "\n".join(f"{n}: {d} (Price {p})" for n, d, p in hits)
    return f"{txt}\n\n[Reference docs]\n{refs}\n"

@function_tool(
    name="schedule_appointment",
    description="Book a 30-minute consultation slot once the patient name and ISO start time are agreed."
)
async def schedule_appointment(
    context: RunContext,
    patient: str,
    iso_start: str,
    notes: str | None = None,
) -> str:
    start_dt = dt.datetime.fromisoformat(iso_start)
    if not start_dt.tzinfo:
        start_dt = TZ.localize(start_dt)
    else:
        start_dt = start_dt.astimezone(TZ)

    slots = free_slots(start_dt.date())

    match = next((s for s in slots if abs((s - start_dt).total_seconds()) < 60), None)
    if not match:
        return "⛔ That slot is unavailable or outside clinic hours."

    link = book(match.isoformat(), patient, notes or "Booked by AI receptionist")
    hour_fmt = match.strftime("%I:%M %p").lstrip("0")
    context.session.say(
        f"Great, {patient}! You’re confirmed for {match.strftime('%A')} at {hour_fmt}. You’ll receive a confirmation shortly."
    )
    return f"Booked at {match.isoformat()}. Link: {link}"

class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=DENTAL_RECEPTIONIST_PROMPT,
            stt=deepgram.STT(),
            llm=LLM(model="gpt-4.1-nano-2025-04-14"),
            tts=cartesia.TTS(),
            tools=[schedule_appointment],
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