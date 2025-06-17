"""
mailer.py  ▸  Simple SMTP helper for the dental AI receptionist.

Environment variables required:
    SMTP_HOST   = smtp.gmail.com
    SMTP_PORT   = 587           (TLS)
    SMTP_USER   = your@email.com
    SMTP_PASS   = app-password  (Gmail “App password” or real SMTP cred)
    SMTP_FROM   = "Arlington Dental Clinic <reception@yourdomain.com>"
"""
import os, smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

_ctx = ssl.create_default_context()

def send_confirmation(to_addr: str, patient: str, when_str: str, link: str):
    """
    Sends a plain-text confirmation email.
    • to_addr   – patient email
    • patient   – full name
    • when_str  – “Tuesday 11 June 2025 at 11:00 AM”
    • link      – Google-Calendar HTML link
    """
    msg = EmailMessage()
    msg["Subject"] = "🦷 Your dental appointment is confirmed"
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_addr

    msg.set_content(
f"""Hello {patient},

Your appointment has been booked successfully for {when_str}.

You can view or add it to your calendar here:
{link}

If you need to make any changes, just reply to this email
and our team will be happy to help.

We look forward to seeing you!

— Arlington Dental Clinic Reception
"""
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls(context=_ctx)
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
