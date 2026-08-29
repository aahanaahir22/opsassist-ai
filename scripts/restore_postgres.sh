#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
test -f "$BACKUP_FILE"
test -f "$BACKUP_FILE.sha256"
sha256sum -c "$BACKUP_FILE.sha256"
gzip -dc "$BACKUP_FILE" | psql --set ON_ERROR_STOP=on "$DATABASE_URL"
psql "$DATABASE_URL" --set ON_ERROR_STOP=on -c 'SELECT 1 FROM alembic_version LIMIT 1;'
echo "Restore verification passed."
