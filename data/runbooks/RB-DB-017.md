document_id: RB-DB-017
version: 3.4
title: PostgreSQL connection-pool exhaustion
services: checkout, postgres
type: runbook
trust: verified
---
# PostgreSQL connection-pool exhaustion

## 4.1 Diagnosis

Compare pool acquire latency, active and idle connections, application request latency, and the most recent deployment. A pool occupancy spike alone is insufficient: require a trace that localizes wait time to connection acquisition or an application timeout matching the pool signature.

## 4.2 Safe recovery

If acquire wait rises immediately after a deployment and provider latency remains nominal, prefer rolling back the implicated application version before increasing the pool ceiling. Drain traffic, preserve at least two healthy replicas, and restart sequentially only inside the simulator. Verify p95 latency below 250 milliseconds, error rate below one percent, and pool occupancy below seventy percent for three consecutive windows.

Never delete the database, terminate all sessions, or represent an attempted action as recovered before verification telemetry arrives.
