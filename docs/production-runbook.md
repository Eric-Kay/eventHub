# EventHub Production Runbook

## Pre-deploy
- confirm images exist in registry
- confirm migrations reviewed
- confirm secrets present
- confirm ingress and certs present
- confirm metrics and logs working

## Deploy
- run CI
- push images
- sync ArgoCD app
- verify rollout
- verify app health endpoints
- verify worker connectivity
- verify RabbitMQ queues
- verify PostgreSQL and Redis health

## Rollback
- rollback ArgoCD revision or Helm release
- scale down broken canary
- restore previous image tag

## Post-deploy checks
- login works
- booking creation works
- payment worker confirms booking
- ticket PDF generation works
- metrics endpoint reachable
- dashboards populated
