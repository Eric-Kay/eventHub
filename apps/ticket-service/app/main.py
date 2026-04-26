import uuid
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import qrcode
from reportlab.pdfgen import canvas
from .db import Base, engine, get_db
from .models import Ticket
from app.ticket_utils import generate_ticket_assets
from app.worker import run_worker_in_background


Base.metadata.create_all(bind=engine)
app = FastAPI(title="ticket-service")
ARTIFACT_DIR = Path("/tmp/eventhub_tickets")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
def startup():
    run_worker_in_background()

class IssueTicket(BaseModel):
    booking_id: int
    event_id: int
    user_id: int

def generate_qr_png(ticket_code: str, output_path: Path):
    img = qrcode.make(ticket_code)
    img.save(output_path)

def generate_pdf(ticket_code: str, booking_id: int, event_id: int, user_id: int, output_path: Path):
    c = canvas.Canvas(str(output_path))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 780, "EventHub Ticket")
    c.setFont("Helvetica", 12)
    c.drawString(72, 740, f"Ticket Code: {ticket_code}")
    c.drawString(72, 720, f"Booking ID: {booking_id}")
    c.drawString(72, 700, f"Event ID: {event_id}")
    c.drawString(72, 680, f"User ID: {user_id}")
    c.showPage()
    c.save()

@app.get("/health")
def health():
    return {"status": "ok", "service": "ticket-service"}

@app.post("/tickets/issue")
def issue(payload: IssueTicket, db: Session = Depends(get_db)):
    existing = db.query(Ticket).filter(Ticket.booking_id == payload.booking_id).first()
    if existing:
        return existing
    code = f"TKT-{uuid.uuid4().hex[:12].upper()}"
    qr_path = ARTIFACT_DIR / f"{code}.png"
    pdf_path = ARTIFACT_DIR / f"{code}.pdf"
    generate_qr_png(code, qr_path)
    generate_pdf(code, payload.booking_id, payload.event_id, payload.user_id, pdf_path)
    ticket = Ticket(
        booking_id=payload.booking_id,
        event_id=payload.event_id,
        user_id=payload.user_id,
        ticket_code=code,
        qr_path=str(qr_path),
        pdf_path=str(pdf_path),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@app.get("/tickets")
def list_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).all()
    

@app.get("/tickets/{ticket_id}/pdf")
def download_ticket_pdf(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return FileResponse(ticket.pdf_path, media_type="application/pdf", filename=f"{ticket.ticket_code}.pdf")

