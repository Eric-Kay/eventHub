import os
import time
import psycopg2

host = os.getenv("POSTGRES_HOST", "postgres")
port = os.getenv("POSTGRES_PORT", "5432")
db = os.getenv("POSTGRES_DB", "eventhub")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")

for attempt in range(30):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=db,
            user=user,
            password=password,
        )
        conn.close()
        print("Postgres is ready")
        break
    except Exception as e:
        print(f"Waiting for Postgres... {attempt + 1}/30")
        time.sleep(2)
else:
    raise SystemExit("Postgres was not ready after 60 seconds")