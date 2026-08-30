FROM postgres:17-alpine
RUN apk add --no-cache bash gzip coreutils
COPY scripts/backup_postgres.sh /usr/local/bin/backup-postgres
ENTRYPOINT ["bash", "/usr/local/bin/backup-postgres"]
