document_id: RB-CACHE-009
version: 1.8
title: Cache stampede containment
services: checkout, redis, postgres
type: runbook
trust: reviewed
---
# Cache stampede containment

Correlate cache miss rate with database concurrency and shared traces. Use request coalescing, randomized expiry jitter, and a bounded stale-while-revalidate window. Do not flush a real production cache. Verify miss rate and database latency over three synthetic telemetry windows.
