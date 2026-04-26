import json
import os
import uuid

import pika
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from .models import Payment
from .rabbit import publish

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="payment-service")


class PaymentCreate(BaseModel):
    booking_id: int
    amount: float
    payment_method: str = "card"


def publish_payment_success(payment: Payment):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )

    channel = connection.channel()

    channel.exchange_declare(
        exchange="payments",
        exchange_type="topic",
        durable=True,
    )

    message = {
        "payment_id": payment.id,
        "booking_id": payment.booking_id,
        "amount": float(payment.amount),
        "status": payment.status,
        "user_id": 3,
        "event_id": 1,
    }

    channel.basic_publish(
        exchange="payments",
        routing_key="payment.success",
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    print(
        f"Published payment.success for booking_id={payment.booking_id}",
        flush=True,
    )

    connection.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "payment-service"}


@app.post("/payments")
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    payment = Payment(
        booking_id=payload.booking_id,
        amount=payload.amount,
        status="SUCCESS",
        transaction_ref=str(uuid.uuid4()),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    event = {
        "booking_id": payment.booking_id,
        "payment_id": payment.id,
        "amount": float(payment.amount),
        "status": payment.status,
    }

    publish_payment_success(payment)

    publish("payment_success_queue", event)
    publish("analytics_queue", {"type": "payment_success", **event})
    publish("notification_queue", {"type": "payment_success", **event})

    return {"payment_id": payment.id, "status": payment.status}