import os
import json
import pika
from fastapi import FastAPI

app = FastAPI(title="notification-service")

def get_messages(queue_name: str):
    creds = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest")
    )
    conn = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=creds
        )
    )
    ch = conn.channel()
    ch.queue_declare(queue=queue_name, durable=True)
    messages = []
    while True:
        method, properties, body = ch.basic_get(queue=queue_name, auto_ack=False)
        if not method:
            break
        payload = json.loads(body.decode())
        messages.append(payload)
        ch.basic_nack(method.delivery_tag, requeue=True)
        break
    conn.close()
    return messages

@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}

@app.get("/notifications/failed")
def failed():
    return {
        "dead_letter_queue_messages_preview": get_messages("notification_dlq")
    }
