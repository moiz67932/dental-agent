from dotenv import load_dotenv
from twilio.rest import Client
import os

load_dotenv()
_SID   = os.getenv("TWILIO_ACCOUNT_SID")
_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
_FROM  = os.getenv("TWILIO_FROM_NUMBER")

_client = Client(_SID, _TOKEN)

def send_sms(to: str, body: str) -> str:
    msg = _client.messages.create(body=body, from_=_FROM, to=to)
    return msg.sid
