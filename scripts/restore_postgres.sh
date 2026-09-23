#!/bin/sh
set -eu

: "${DATABASE_URL:?DATABASE_URL is required}"
BACKUP_FILE="${1:?Usage: restore_postgres.sh <backup-file>}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

echo "WARNING: this replaces database objects/data in the target database."
printf "Type RESTORE to continue: "
read confirmation
if [ "$confirmation" != "RESTORE" ]; then
  echo "Restore cancelled."
  exit 1
fi

pg_restore "$DATABASE_URL" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  "$BACKUP_FILE"

echo "Restore completed. Run: alembic upgrade head"
