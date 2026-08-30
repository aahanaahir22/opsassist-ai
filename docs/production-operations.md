# Production-like operations

## Service topology

The intended Railway topology is `opsassist-api`, PostgreSQL, Redis, `opsassist-indexer`, `opsassist-otel`, `opsassist-prometheus` and `opsassist-grafana`. The indexer owns a persistent `/indexes` volume and serves Sentence Transformer + FAISS retrieval over the private network. The observability services use Railway's private DNS; only the API should be public by default.

## Release and migrations

The API must gate process startup on an Alembic upgrade:

```bash
sh -c 'cd /workspace/apps/api && python -m alembic -c alembic.ini upgrade head && exec uvicorn app.main:app --app-dir /workspace/apps/api --host 0.0.0.0 --port 8000'
```

Railway runs this inside the application container so private database networking is available. Uvicorn never starts if the migration fails. Production sets `OPSASSIST_AUTO_CREATE_SCHEMA=false`; `Base.metadata.create_all()` never substitutes for migrations. Keep the API at one replica while using this startup gate, or move the same Alembic command to a serialized release job before scaling horizontally. CI upgrades an empty database to head twice to prove idempotence.

## Backups and restore drills

`scripts/backup_postgres.sh` creates a compressed logical backup and SHA-256 sidecar. Production should copy both to encrypted object storage under a separate retention policy. `scripts/test_restore.sh` backs up the source and restores into an explicitly supplied disposable database; it refuses to invent the restore target. Run a restore drill after schema changes and at least monthly.

## Deployment rollback

1. Stop rollout if readiness or migration checks fail.
2. In Railway, redeploy the last known-good image/commit for the affected service.
3. Do not downgrade the database automatically. Use a tested forward-fix migration unless a reviewed downgrade is explicitly safe.
4. Confirm `/api/v1/ready`, request error rate, p95 latency and agent failure alerts.
5. Rebuild or select the previous FAISS index version by changing `current.json` atomically.
6. Record the rollback commit, operator and verification evidence in the change record.

## Observability and alerts

The API exposes Prometheus metrics at `/metrics` and exports traces through OTLP/HTTP when configured. Prometheus rules cover 5xx rate, p95 latency and repeated agent-provider failures; the provisioned Grafana dashboard shows the same service-level signals. Configure an external Sentry DSN for exception monitoring and route Prometheus alerts to a real notification receiver before calling the environment production-ready.

## Simulator boundary

The incident workflow can read synthetic or explicitly ingested telemetry, but action execution always targets the deterministic `DigitalTwin`. The repository contains no adapter for Kubernetes, AWS, Azure, GCP, SSH or a customer control plane. Every simulation result and execution response remains labelled as an estimate or simulator-only result.
