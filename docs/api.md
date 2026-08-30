# API

OpenAPI is served at `/docs` and ReDoc at `/redoc`. The versioned prefix is `/api/v1`.

Core resources include telemetry ingestion, incidents, evidence, hypotheses, timeline, simulations, approvals, execution, verification, knowledge search, evaluations, topology, postmortems and audit. Errors use:

```json
{"error":{"code":"POLICY_APPROVAL_REQUIRED","message":"Incident Commander approval is required.","request_id":"req_...","details":{}}}
```

The event socket is `/api/v1/events?incident_id=...`. Clients should reconnect with bounded exponential backoff and refetch incident state because events are progress notifications, not the source of truth.
