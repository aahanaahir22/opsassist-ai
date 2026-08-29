#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?DATABASE_URL is required}"
backup_dir="${BACKUP_DIR:-/backups}"
retention_days="${BACKUP_RETENTION_DAYS:-14}"
mkdir -p "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$backup_dir/opsassist-$timestamp.sql.gz"
pg_dump --format=plain --no-owner --no-acl "$DATABASE_URL" | gzip -9 > "$target"
sha256sum "$target" > "$target.sha256"
find "$backup_dir" -type f -name 'opsassist-*.sql.gz*' -mtime "+$retention_days" -delete
echo "Backup created: $target"
