from pydantic import BaseModel
from datetime import datetime

class EventCreate(BaseModel):
    organizer_id: int
    title: str
    description: str
    category: str
    venue: str
    city: str
    start_time: datetime
    end_time: datetime
    total_tickets: int
    price: float

class EventOut(BaseModel):
    id: int
    title: str
    category: str
    city: str
    venue: str
    available_tickets: int
    price: float
    status: str
