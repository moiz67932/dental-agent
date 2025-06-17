import json
from .calendar_utils import book

# ------------------ UPDATED SPEC ------------------
FUNC_SPEC = {
    "name": "schedule_appointment",
    "description": "Book a dental appointment when NAME, EMAIL, and ISO start are known.",
    "parameters": {
        "type": "object",
        "properties": {
            "iso_start": {"type": "string", "description": "ISO 8601 start time in clinic TZ"},
            "patient":   {"type": "string", "description": "Patient full name"},
            "email":     {"type": "string", "description": "Patient email address"},
            "notes":     {"type": "string"},
        },
        "required": ["iso_start", "patient", "email"],
    },
}
# ---------------------------------------------------

def run_tool_if_called(msg):
    """Intercept OpenAI chat-completion response and run booking if requested."""
    if msg.choices[0].finish_reason != "function_call":
        return None

    fc = msg.choices[0].message.function_call
    if fc.name != "schedule_appointment":
        return None

    args = json.loads(fc.arguments)
    slot = args["iso_start"]
    patient = args["patient"]
    email = args["email"]               # <- parsed (not used further here)
    link = book(slot, patient, args.get("notes", f"Booked by AI – {email}"))
    return (
        f"✅ Done! Your consultation is booked for {slot}. "
        f"You’ll receive a confirmation shortly. {link}"
    )
