#!/bin/sh
set -eu

# Free-tier deployments do not provide a separate pre-deploy hook.
# Keep schema changes explicit via Alembic rather than running DDL during
# application import/startup.
alembic upgrade head

exec fastapi run apps/api/app/main.py --host 0.0.0.0 --port "${PORT:-10000}" --proxy-headers
