---
id: RB-CHK-002
title: Checkout API - Upstream Dependency Failure
service: checkout-api
---
# Upstream 503 handling
Guidance for sustained dependency failure.
## Detection signals
Group repeated HTTP 503 responses by dependency, route, and deployment version. Confirm that the failure is not caused by checkout itself.
## Circuit breaker procedure
Enable only the approved circuit-breaker policy and bounded fallback. This state-changing action requires a named human approval.
## Verification
Verify fallback traffic, checkout completion rate, and upstream error rate. Disable the circuit breaker if data-integrity risk appears.

