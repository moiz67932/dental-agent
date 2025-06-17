# whatsapp_sender.py  – Send a pre-approved WhatsApp template via Twilio
import os, json
from dotenv import load_dotenv
from twilio.rest import Client
load_dotenv()

# _SID   = os.getenv("TWILIO_ACCOUNT_SID")
# _TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# _FROM  = f"whatsapp:{os.getenv('TWILIO_FROM_NUMBER')}"
# _TEMPLATE_SID = os.getenv("TWILIO_TEMPLATE_SID")  # e.g. HXxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# _client = Client(_SID, _TOKEN)

# def send_wa(to: str, params: list[str]) -> str:
#     """
#     Send the approved WhatsApp template referenced by TWILIO_TEMPLATE_SID.
#       to      – E.164, e.g. +923001234567  (without the 'whatsapp:' prefix)
#       params  – ordered substitution strings {{1}}, {{2}} …
#     Returns Twilio Message SID.
#     """
#     to = f"whatsapp:{to}"
#     # Twilio expects a *stringified* JSON object in content_variables.
#     vars_json = json.dumps({f"{{{{{i+1}}}}}": p for i, p in enumerate(params)})
#     msg = _client.messages.create(
#         from_=_FROM,
#         to=to,
#         content_sid=_TEMPLATE_SID,
#         content_variables=vars_json,
#     )
#     return msg.sid




def send_wa(to: str, body: str):
    from twilio.rest import Client
    _SID   = os.getenv("TWILIO_ACCOUNT_SID")
    _TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    _FROM  = f"whatsapp:{os.getenv('TWILIO_FROM_NUMBER')}"
    client = Client(_SID, _TOKEN)
    client.messages.create(
        from_=_FROM,
        to=f"whatsapp:{to}",
        body=body,
    )
    return "Message sent successfully"