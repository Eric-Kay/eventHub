import json
import time
from app.rabbit import rabbit_connection

MAX_RETRIES = 3

def callback(ch, method, properties, body):
    payload = json.loads(body.decode())
    retries = int(payload.get("retries", 0))
    try:
        print(f"Sending notification: {payload}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        if retries >= MAX_RETRIES:
            payload["dead_lettered"] = True
            ch.queue_declare(queue="notification_dlq", durable=True)
            ch.basic_publish(exchange="", routing_key="notification_dlq", body=json.dumps(payload).encode())
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            payload["retries"] = retries + 1
            ch.basic_publish(exchange="", routing_key="notification_queue", body=json.dumps(payload).encode())
            ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    while True:
        try:
            conn = rabbit_connection()
            ch = conn.channel()
            ch.queue_declare(queue="notification_queue", durable=True)
            ch.queue_declare(queue="notification_dlq", durable=True)
            ch.basic_consume(queue="notification_queue", on_message_callback=callback)
            print("Notification worker started...")
            ch.start_consuming()
        except Exception as e:
            print("Worker retrying after error:", e)
            time.sleep(5)
