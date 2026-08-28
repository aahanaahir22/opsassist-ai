# API examples

Interactive OpenAPI documentation is available at `/docs` when the backend runs.

## Ingest an event

```json
{
  "service": "payment-api",
  "environment": "production",
  "severity": "critical",
  "message": "Timed out acquiring PostgreSQL connection after 2000 ms",
  "error_code": "DB_TIMEOUT",
  "trace_id": "tr_7ef029a1",
  "attributes": {"pool_active": 40, "pool_max": 40, "pool_waiters": 126}
}
```

## Typed action plan

```json
{
  "action_type": "restart_connection_pool_workers",
  "target": "payment-api",
  "summary": "Recycle payment API workers in a rolling sequence, then verify pool saturation.",
  "risk": "sensitive",
  "parameters": {"strategy": "rolling", "max_unavailable": 1, "verify_seconds": 30},
  "evidence_ids": ["RB-PAY-001#connection-pool-exhaustion", "RB-PAY-001#verification"]
}
```

## Policy decision

```json
{
  "decision": "approval_required",
  "reason": "State-changing remediation requires a named human approver.",
  "policy": "OPS-POLICY-001"
}
```

## Environment variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `OPSASSIST_DATABASE_URL` | `sqlite:///./opsassist.db` | SQLAlchemy connection URL |
| `OPSASSIST_CORS_ORIGINS` | local frontend URLs | Comma-separated origins |
| `OPSASSIST_API_KEY` | empty | Optional `X-API-Key` value |
| `OPSASSIST_SEED_DEMO` | `true` | Seed the demo when the database is empty |

