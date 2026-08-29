# Architecture

The browser preserves the original 3D/motion-heavy experience and talks through `lib/opsassist-api.ts`. FastAPI owns validation, request IDs, rate limits, orchestration and policy. SQLAlchemy stores incidents, simulations, approvals, executions, audit events, verification and postmortems. Numerical detectors and retrieval remain independent from optional language models.

The Checkout path is: scenario loader → anomaly service → evidence → weighted ranking → typed agents → graph simulation → backend policy → signed approval → idempotent synthetic executor → three verification windows → cited postmortem. WebSocket events expose milestones without exposing private reasoning.

PostgreSQL is the Compose default. SQLite is the local fallback. `OPSASSIST_DATABASE_URL` selects the backend.
