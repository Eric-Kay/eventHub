import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import redis
import requests
from .db import Base, engine, get_db
from .models import Booking
from .rabbit import publish
from .auth import get_current_user

Base.metadata.create_all(bind=engine)
app = FastAPI(title="booking-service")
TTL = int(os.getenv("BOOKING_TTL_SECONDS", "600"))
EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "http://event-service:8000")
r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)

class BookingCreate(BaseModel):
    user_id: int
    event_id: int
    quantity: int
    total_amount: float

@app.get("/health")
def health():
    return {"status": "ok", "service": "booking-service"}

@app.post("/bookings")
def create_booking(payload: BookingCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] not in ["customer", "admin", "organizer"]:
        raise HTTPException(status_code=403, detail="forbidden")
    reserve = requests.post(
        f"{EVENT_SERVICE_URL}/events/{payload.event_id}/reserve",
        params={"quantity": payload.quantity},
        timeout=20
    )
    if reserve.status_code >= 400:
        raise HTTPException(status_code=reserve.status_code, detail=reserve.text)

    expires_at = datetime.utcnow() + timedelta(seconds=TTL)
    booking = Booking(
        user_id=payload.user_id,
        event_id=payload.event_id,
        quantity=payload.quantity,
        total_amount=payload.total_amount,
        expires_at=expires_at,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    r.setex(f"booking_hold:{booking.id}", TTL, "active")
    publish("notification_queue", {"type": "booking_created", "booking_id": booking.id, "user_id": booking.user_id})
    return {"booking_id": booking.id, "status": booking.status, "expires_at": expires_at.isoformat(), "ttl_seconds": TTL}

@app.get("/bookings")
def list_bookings(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] == "admin":
        return db.query(Booking).all()
    return db.query(Booking).filter(Booking.user_id == user["user_id"]).all()

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="booking not found")
    if user["role"] != "admin" and booking.user_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="forbidden")
    return {
        "id": booking.id,
        "status": booking.status,
        "ttl_seconds": r.ttl(f"booking_hold:{booking.id}"),
        "event_id": booking.event_id,
        "user_id": booking.user_id,
        "quantity": booking.quantity,
        "total_amount": float(booking.total_amount),
    }

@app.post("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="booking not found")
    booking.status = "CONFIRMED"
    db.commit()
    r.delete(f"booking_hold:{booking.id}")
    publish("notification_queue", {"type": "booking_confirmed", "booking_id": booking.id, "user_id": booking.user_id})
    return {"id": booking.id, "status": booking.status}

@app.post("/bookings/{booking_id}/expire")
def expire_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="booking not found")
    if booking.status == "EXPIRED":
        return {"id": booking.id, "status": booking.status}
    booking.status = "EXPIRED"
    db.commit()
    r.delete(f"booking_hold:{booking.id}")
    requests.post(
        f"{EVENT_SERVICE_URL}/events/{booking.event_id}/release",
        params={"quantity": booking.quantity},
        timeout=20
    )
    publish("notification_queue", {"type": "booking_expired", "booking_id": booking.id, "user_id": booking.user_id})
    return {"id": booking.id, "status": booking.status}
