# Checkout demo walkthrough

1. Start PostgreSQL, the API and the web app with Docker Compose.
2. Open API docs and confirm `/health` and `/ready`.
3. Launch `checkout_pool_exhaustion` from Mission Control.
4. Watch WebSocket agent milestones, then inspect exact evidence IDs and ranking components.
5. Search for “database pool rollback” and open the returned `RB-DB-017` chunk citation.
6. Simulate `rollback_deployment` for Checkout with target version `v2.18.0`.
7. Attempt execution without approval and observe `POLICY_APPROVAL_REQUIRED`.
8. Approve as `incident_commander`, execute with an idempotency key, and submit verification.
9. Confirm the incident reaches `VERIFIED` only after three windows.
10. Open the generated postmortem and inspect citations and audit history.

Everything in this walkthrough operates on checked-in synthetic data.
