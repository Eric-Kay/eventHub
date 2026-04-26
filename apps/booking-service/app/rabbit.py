import os, json, pika

def rabbit_connection():
    creds = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest")
    )
    return pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "localhost"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=creds
        )
    )

def publish(queue: str, payload: dict):
    conn = rabbit_connection()
    ch = conn.channel()
    ch.queue_declare(queue=queue, durable=True)
    ch.basic_publish(exchange="", routing_key=queue, body=json.dumps(payload).encode())
    conn.close()
