import json, datetime as dt, os
from openai import OpenAI
from .calendar_utils import book

client = OpenAI()

FUNC_SPEC = {
    "name": "schedule_appointment",
    "description": "Book a dental appointment when all details are known.",
    "parameters": {
        "type": "object",
        "properties": {
            "iso_start": {"type": "string", "description": "ISO 8601 start time in clinic TZ"},
            "patient":   {"type": "string", "description": "Patient full name"},
            "notes":     {"type": "string"}
        },
        "required": ["iso_start", "patient"]
    }
}

def run_tool_if_called(msg):
    """Intercept OpenAI chat completion response and run booking if requested."""
    if msg.choices[0].finish_reason != "function_call":
        return None  # nothing to do

    fc = msg.choices[0].message.function_call
    if fc.name != "schedule_appointment":
        return None

    args = json.loads(fc.arguments)
    slot = args["iso_start"]
    link = book(slot, args["patient"], args.get("notes","Booked by AI"))
    return (
        f"✅ Done! Your consultation is booked for {slot}. "
        f"You’ll receive a confirmation shortly. {link}"
    )
