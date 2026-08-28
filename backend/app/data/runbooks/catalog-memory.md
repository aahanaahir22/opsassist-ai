---
id: RB-CAT-003
title: Catalog API - Worker Memory Pressure
service: catalog-api
---
# Memory pressure response
Approved capacity guidance for catalog workers.
## Detection signals
Confirm container restart count, memory working set, request latency, and deployment changes across multiple observations.
## Bounded scaling
Add one replica only when allow-listed and below the maximum limit. Scaling requires human approval.
## Verification
Verify readiness, reduced memory utilization, stable error rate, and even traffic distribution.

