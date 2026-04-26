#!/usr/bin/env sh
set -eu
echo "Running migration scaffolds..."
for svc in auth-service event-service booking-service payment-service ticket-service; do
  echo "Migration placeholder for $svc"
done
echo "Done."
