import time
import os
import redis
import requests
from app.db import SessionLocal
from app.models import Booking

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", "6379")), decode_responses=True)
EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "http://event-service:8000")

def sweep():
    db = SessionLocal()
    try:
        for booking in db.query(Booking).filter(Booking.status == "PENDING").all():
            if r.ttl(f"booking_hold:{booking.id}") == -2:
                booking.status = "EXPIRED"
                try:
                    requests.post(
                        f"{EVENT_SERVICE_URL}/events/{booking.event_id}/release",
                        params={"quantity": booking.quantity},
                        timeout=20
                    )
                except Exception as exc:
                    print("inventory release failed:", exc)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting booking expiry worker...")
    while True:
        sweep()
        time.sleep(5)
