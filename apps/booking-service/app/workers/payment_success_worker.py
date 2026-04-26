import json
import time
import os
import requests
from app.rabbit import rabbit_connection
from app.db import SessionLocal
from app.models import Booking

TICKET_URL = os.getenv("TICKET_SERVICE_URL", "http://ticket-service:8000")

def callback(ch, method, properties, body):
    payload = json.loads(body.decode())
    booking_id = payload["booking_id"]
    db = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking and booking.status != "CONFIRMED":
            booking.status = "CONFIRMED"
            db.commit()
            requests.post(
                f"{TICKET_URL}/tickets/issue",
                json={
                    "booking_id": booking.id,
                    "event_id": booking.event_id,
                    "user_id": booking.user_id
                },
                timeout=20
            )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as exc:
        print("payment_success_worker error:", exc)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()

if __name__ == "__main__":
    while True:
        try:
            conn = rabbit_connection()
            ch = conn.channel()
            ch.queue_declare(queue="payment_success_queue", durable=True)
            ch.basic_consume(queue="payment_success_queue", on_message_callback=callback)
            print("Payment success worker started...")
            ch.start_consuming()
        except Exception as e:
            print("Worker retrying after error:", e)
            time.sleep(5)
