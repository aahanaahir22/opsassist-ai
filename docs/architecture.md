# Architecture

The browser preserves the original 3D/motion-heavy experience and talks through `lib/opsassist-api.ts`. FastAPI owns validation, request IDs, rate limits, orchestration and policy. SQLAlchemy stores incidents, simulations, approvals, executions, audit events, verification and postmortems. Numerical detectors and retrieval remain independent from optional language models.

The Checkout path is: scenario loader → anomaly service → evidence → weighted ranking → typed agents → graph simulation → backend policy → signed approval → idempotent synthetic executor → three verification windows → cited postmortem. WebSocket events expose milestones without exposing private reasoning.

PostgreSQL is the production default. SQLite is the local fallback. `OPSASSIST_DATABASE_URL` selects the backend. Auth0 Organization `org_id` becomes the tenant boundary and every incident, audit and telemetry query includes it. The API delegates semantic retrieval to a persistent FAISS indexer, uses Redis for distributed rate limits, and emits metrics/traces through Prometheus and OpenTelemetry.

The production data path is intentionally separate from the remediation target: logs and traces may be ingested through typed APIs or an OTel Collector, but every rollback, restart, scale or integration-disable action is applied only to `DigitalTwin`. No Kubernetes, cloud-control-plane or customer credential adapter is shipped.
