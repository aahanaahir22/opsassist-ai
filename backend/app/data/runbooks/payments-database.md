---
id: RB-PAY-001
title: Payment API - PostgreSQL Connection Pool Exhaustion
service: payment-api
---
# Payment database saturation
Approved operational guidance for payment API database acquisition failures.
## Detection signals
Connection acquisition timeouts combined with active connections equal to the configured pool maximum indicate pool exhaustion. Confirm rising pool waiters, elevated p95 latency, and a sustained request error rate before proposing remediation.
## Connection pool exhaustion
If database health is normal and pool waiters continue to rise, a rolling recycle of application workers can release leaked or stale connections. Never restart every replica simultaneously. Preserve at least one available replica and monitor checkout success.
## Verification
After a rolling recycle, verify pool utilization below seventy-five percent, zero pool waiters, lower p95 latency, and payment error rate within the SLO for at least thirty seconds. Confirm only observed state.
## Rollback and escalation
Stop if payment availability worsens. Escalate when saturation returns within ten minutes, the database is unhealthy, or confidence is below the policy threshold.

