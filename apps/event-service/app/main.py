from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import Event
from .schemas import EventCreate, EventOut
from .auth import get_current_user
from .metrics import metrics_response
from app.db import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="event-service")

@app.get("/health")
def health():
    return {"status": "ok", "service": "event-service"}

@app.get("/metrics")
def metrics():
    return metrics_response("event-service")

@app.post("/events")
def create_event(payload: EventCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] not in ["organizer", "admin"]:
        raise HTTPException(status_code=403, detail="only organizer or admin can create events")
    event = Event(
        organizer_id=payload.organizer_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        venue=payload.venue,
        city=payload.city,
        start_time=payload.start_time,
        end_time=payload.end_time,
        total_tickets=payload.total_tickets,
        available_tickets=payload.total_tickets,
        price=payload.price,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id}

@app.get("/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()

@app.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    return event

@app.get("/events/search", response_model=list[EventOut])
def search_events(q: str | None = None, city: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Event)
    if q:
        query = query.filter(Event.title.ilike(f"%{q}%"))
    if city:
        query = query.filter(Event.city == city)
    if category:
        query = query.filter(Event.category == category)
    return query.all()

@app.post("/events/{event_id}/reserve")
def reserve_inventory(event_id: int, quantity: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).with_for_update().first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    if event.available_tickets < quantity:
        raise HTTPException(status_code=400, detail="not enough tickets available")
    event.available_tickets -= quantity
    db.commit()
    db.refresh(event)
    return {"event_id": event.id, "available_tickets": event.available_tickets}

@app.post("/events/{event_id}/release")
def release_inventory(event_id: int, quantity: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="event not found")
    event.available_tickets = min(event.total_tickets, event.available_tickets + quantity)
    db.commit()
    db.refresh(event)
    return {"event_id": event.id, "available_tickets": event.available_tickets}

@app.get("/organizers/{organizer_id}/events")
def organizer_events(organizer_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user["role"] not in ["organizer", "admin"]:
        raise HTTPException(status_code=403, detail="forbidden")
    return db.query(Event).filter(Event.organizer_id == organizer_id).all()
