---
id: RB-GEN-004
title: General Service Degradation Triage
service: all
---
# Safe evidence collection
General guidance for ambiguous incidents.
## Minimum evidence
Collect service, environment, error code, trace IDs, deployment version, latency percentiles, and a bounded log window. Remove secrets and personal data.
## Low-confidence handling
When confidence is below the threshold, do not mutate infrastructure. Collect diagnostics and route to a human operator with explicit uncertainty.
## Audit requirements
Record grouping, evidence IDs, confidence, policy, approval identity, simulated execution, and verified post-action state.

