#!/usr/bin/env bash
# deploy-staging.sh — Staging deployment script for the Test Conf Website
#
# PURPOSE
#   Pulls the latest Docker images for the staging environment and restarts
#   the Compose stack. Runs database migrations via the backend container
#   after the stack comes up.
#
# HOW IT IS INVOKED
#   This script is set as a forced command in the SSH authorized_keys entry
#   of the 'deploy-test-conf-staging' system user. It is therefore run
#   automatically every time the GitHub Actions deploy workflow connects via
#   SSH. No interactive shell access is granted to that user.
#
# SERVER INSTALLATION
#   1. Copy this file to the server:
#        sudo cp ops/deploy-staging.sh /usr/local/bin/deploy-test-conf-staging.sh
#        sudo chmod +x /usr/local/bin/deploy-test-conf-staging.sh
#   2. Reference it in /home/deploy-test-conf-staging/.ssh/authorized_keys:
#        command="/usr/local/bin/deploy-test-conf-staging.sh",no-port-forwarding,no-agent-forwarding,no-pty <public-key>

set -euo pipefail

cd /var/www/vhosts/test-conf.de/staging.test-conf.de

# Stop database and remove its volume to completely wipe its contents:
ENVIRONMENT=staging docker compose down postgres -v
ENVIRONMENT=staging docker compose pull
ENVIRONMENT=staging docker compose up -d --wait --force-recreate
# Run database migrations:
ENVIRONMENT=staging docker compose exec -T backend alembic upgrade head
# Seed database with dev data:
ENVIRONMENT=staging docker compose exec -T backend python -m backend.seed.cli dev
docker image prune -f
