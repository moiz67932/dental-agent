# test_booking.py

from datetime import datetime
from calendar_utils import book

if __name__ == "__main__":
    # Define test values
    slot_time = "2025-06-11T09:00:00+05:00"
    patient_name = "Test Patient"
    notes = "Test booking from calendar_utils test"

    # Call the book function
    try:
        event_link = book(slot=slot_time, patient=patient_name, notes=notes)
        print("✅ Appointment successfully booked!")
        print("📅 View it on Google Calendar:", event_link)
    except Exception as e:
        print("❌ Failed to book appointment:", str(e))
