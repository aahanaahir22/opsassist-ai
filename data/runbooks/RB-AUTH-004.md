document_id: RB-AUTH-004
version: 2.2
title: Authentication certificate rotation
services: gateway, auth
type: runbook
trust: verified
---
# Authentication certificate rotation

Confirm the certificate fingerprint and expiry timestamp from the local verifier. Rotate only the synthetic certificate fixture, restart replicas sequentially, and verify both token-validation success and the authentication failure-rate recovery window. Disabling authentication is prohibited.
