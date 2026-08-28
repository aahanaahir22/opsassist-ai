# Architecture and trust boundaries

## Design objective

OpsAssist AI separates evidence retrieval, diagnosis, policy, approval, and execution so no single model output can directly mutate a target. The included executor is a state simulator; production integrations are intentionally excluded.

## Component map

| Layer | Responsibility | Input | Output |
| --- | --- | --- | --- |
| Ingestion | Validate and normalize telemetry | `EventCreate` JSON | Stored event |
| Correlation | Group by environment, service, error code, and time window | Event | Incident fingerprint |
| State | Persist incidents, events, approvals, and audit entries | Domain objects | SQL rows |
| Retrieval | Search approved runbook chunks | Incident query | Ranked evidence IDs |
| Diagnosis | Select a reproducible root cause and typed plan | Incident + evidence | Root cause, confidence, `ActionPlan` |
| Policy | Enforce allow-list, confidence, and risk class | `ActionPlan` | Allow, approval required, or deny |
| Approval | Store human identity, decision, reason, and timestamp | Pending action | Approval record |
| Execution | Simulate the smallest allowed action | Approved plan | Before/after state |
| Verification | Confirm observed simulator output | Result state | Verified outcome |
| Audit | Record every decision boundary | Workflow events | Queryable history |

## Data flow

1. `POST /events` validates an event with Pydantic.
2. A fingerprint groups matching open events inside a 15-minute window.
3. The retriever chunks Markdown runbooks and creates normalized TF-IDF vectors.
4. `faiss.IndexFlatIP` returns cosine-ranked chunks filtered by service metadata.
5. The diagnosis service produces a root cause, confidence, and typed action.
6. The policy engine checks allow-list membership, confidence, and risk.
7. Sensitive plans create a pending approval and change incident state to `approval_pending`.
8. Execution remains blocked until an approved record exists.
9. The simulator returns explicit before/after state; only observed outcomes are confirmed.
10. Audit entries preserve grouping, evidence IDs, policy, approval, and execution.

## Trust boundaries

- Telemetry is untrusted and validated at the API boundary.
- Runbook content is treated as curated repository data, not an instruction that can bypass policy.
- Diagnosis output is data, never executable code.
- Policy is deterministic application logic.
- Approval is bound to one stored incident and action type.
- The simulator has no credentials and no production network integration.

## Storage modes

SQLite is the default development database. `docker-compose.yml` switches the same SQLAlchemy models to PostgreSQL through `OPSASSIST_DATABASE_URL`.

## Production hardening gaps

This portfolio prototype still needs OAuth/RBAC, schema migrations, distributed correlation, durable queues, tamper-evident audit storage, secret management, network isolation, rate limiting, policy versioning, and reviewed infrastructure adapters before any production use.

