from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

REQUEST_COUNTER = Counter("app_requests_total", "Total requests", ["service"])

def metrics_response(service_name: str):
    REQUEST_COUNTER.labels(service=service_name).inc()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
