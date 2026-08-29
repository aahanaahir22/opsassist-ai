# Production-like operations

## Service topology

The intended Railway topology is `api`, PostgreSQL, Redis and `indexer`. The indexer owns a persistent `/indexes` volume and serves Sentence Transformer + FAISS retrieval over the private network. OTel Collector, Prometheus and Grafana can run as additional services from `infra/`.

## Release and migrations

The API release command is:

```bash
cd /workspace/apps/api
python -m alembic -c alembic.ini upgrade head
```

Production sets `OPSASSIST_AUTO_CREATE_SCHEMA=false`; application startup never substitutes for migrations. CI upgrades an empty database to head twice to prove idempotence.

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
