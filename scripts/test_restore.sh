#!/usr/bin/env bash
set -euo pipefail
: "${SOURCE_DATABASE_URL:?SOURCE_DATABASE_URL is required}"
: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL must target an isolated disposable database}"
temp_dir="$(mktemp -d)"
trap 'rm -rf "$temp_dir"' EXIT
DATABASE_URL="$SOURCE_DATABASE_URL" BACKUP_DIR="$temp_dir" bash scripts/backup_postgres.sh
backup_file="$(find "$temp_dir" -name 'opsassist-*.sql.gz' -print -quit)"
DATABASE_URL="$RESTORE_DATABASE_URL" BACKUP_FILE="$backup_file" bash scripts/restore_postgres.sh
