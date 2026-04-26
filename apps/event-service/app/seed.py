from datetime import datetime, timedelta
from app.db import SessionLocal, Base, engine
from app.models import Event

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Event).count() == 0:
    now = datetime.utcnow()
    db.add_all([
        Event(organizer_id=2, title="Cloud DevOps Summit", description="Talks and workshops",
              category="Tech", venue="Civic Hall", city="Lagos",
              start_time=now + timedelta(days=7), end_time=now + timedelta(days=7, hours=8),
              total_tickets=500, available_tickets=500, price=50.00),
        Event(organizer_id=2, title="Jazz Night Live", description="Evening music event",
              category="Music", venue="Blue Arena", city="Abuja",
              start_time=now + timedelta(days=14), end_time=now + timedelta(days=14, hours=4),
              total_tickets=200, available_tickets=200, price=30.00),
    ])
    db.commit()
db.close()
print("Seeded events")
