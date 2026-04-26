# EventHub Final Phase

This is the final phase of the EventHub implementation roadmap.

## Added in this final phase
- Alembic-wired migration scaffolds
- refresh token flow scaffold
- RBAC notes and middleware starters
- OpenTelemetry starter instrumentation
- Prometheus metrics starter endpoints
- Helm values for dev and prod
- ArgoCD dev and prod app manifests
- Jenkins pipeline starter for EventHub
- Kubernetes secrets/config starter manifests
- production runbook and verification checklist

## Project status
This repo is now a strong portfolio-grade starter platform:
- microservices
- async processing
- ticket generation
- Redis TTL booking expiry
- DLQ starter
- CI starter
- Helm starter
- ArgoCD starter
- canary manifest starter
- auth and RBAC starter
- monitoring/tracing starter

## Start locally

```bash
cp .env.example .env
docker compose up --build
```

## Seed demo data

```bash
docker compose exec auth-service python app/seed.py
docker compose exec event-service python app/seed.py
```

## Workers

```bash
docker compose exec booking-service python app/workers/expiry_worker.py
docker compose exec booking-service python app/workers/payment_success_worker.py
docker compose exec notification-service python app/workers/notification_worker.py
```

## Tests

```bash
docker compose exec auth-service pytest -q
docker compose exec event-service pytest -q
docker compose exec booking-service pytest -q
```

## Important note
This final phase is still a production-style starter, not a fully enterprise-complete commercial platform.
It gives you the architecture, repo layout, CI/CD, GitOps, observability, and service scaffolds needed to finish hardening.
