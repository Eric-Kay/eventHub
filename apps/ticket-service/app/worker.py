import json
import os
import threading
import time

import pika
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Ticket
from app.ticket_utils import generate_ticket_assets

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "ticket-service.payment-success"
EXCHANGE_NAME = "payments"
ROUTING_KEY = "payment.success"


def issue_ticket_from_payment(payload: dict):
    db: Session = SessionLocal()

    try:
        booking_id = int(payload["booking_id"])
        user_id = int(payload.get("user_id", 3))
        event_id = int(payload.get("event_id", 1))

        existing = db.query(Ticket).filter(Ticket.booking_id == booking_id).first()
        if existing:
            print(f"Ticket already exists for booking_id={booking_id}", flush=True)
            return

        ticket_code, qr_path, pdf_path = generate_ticket_assets(
            booking_id=booking_id,
            user_id=user_id,
            event_id=event_id,
        )

        ticket = Ticket(
            booking_id=booking_id,
            user_id=user_id,
            event_id=event_id,
            ticket_code=ticket_code,
            qr_path=qr_path,
            pdf_path=pdf_path,
            status="ISSUED",
        )

        db.add(ticket)
        db.commit()

        print(
            f"Auto-issued ticket {ticket_code} for booking_id={booking_id}",
            flush=True,
        )

    except Exception as e:
        db.rollback()
        print(f"Failed to issue ticket from payload={payload}: {e}", flush=True)
        raise

    finally:
        db.close()


def start_payment_consumer():
    while True:
        connection = None

        try:
            print("Ticket worker connecting to RabbitMQ...", flush=True)

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    heartbeat=30,
                    blocked_connection_timeout=30,
                )
            )

            channel = connection.channel()

            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type="topic",
                durable=True,
            )

            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True,
            )

            channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=QUEUE_NAME,
                routing_key=ROUTING_KEY,
            )

            def callback(ch, method, properties, body):
                try:
                    payload = json.loads(body.decode("utf-8"))
                    print(f"Received payment.success event: {payload}", flush=True)

                    issue_ticket_from_payment(payload)

                    ch.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    print(f"Worker failed message: {e}", flush=True)

                    # Requeue false prevents poison messages from looping forever
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False,
                    )

            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback,
            )

            print("Ticket worker listening for payment.success events", flush=True)

            channel.start_consuming()

        except Exception as e:
            print(f"Ticket worker error: {e}", flush=True)

            try:
                if connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass

            time.sleep(5)


def run_worker_in_background():
    thread = threading.Thread(
        target=start_payment_consumer,
        daemon=True,
        name="payment-success-ticket-worker",
    )
    thread.start()
    print("Ticket worker background thread started", flush=True)