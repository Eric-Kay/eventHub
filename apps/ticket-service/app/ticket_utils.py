import uuid
import os
from pathlib import Path
import qrcode
from reportlab.pdfgen import canvas

BASE_DIR = "/tmp/eventhub_tickets"


def generate_ticket_assets(booking_id, user_id, event_id):
    os.makedirs(BASE_DIR, exist_ok=True)

    ticket_code = f"TKT-{uuid.uuid4().hex[:12].upper()}"

    qr_path = f"{BASE_DIR}/{ticket_code}.png"
    pdf_path = f"{BASE_DIR}/{ticket_code}.pdf"

    qr = qrcode.make(ticket_code)
    qr.save(qr_path)

    c = canvas.Canvas(pdf_path)
    c.drawString(100,750,f"Ticket: {ticket_code}")
    c.drawString(100,720,f"Booking: {booking_id}")
    c.drawString(100,690,f"User: {user_id}")
    c.drawString(100,660,f"Event: {event_id}")
    c.save()

    return ticket_code, qr_path, pdf_path