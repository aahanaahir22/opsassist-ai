document_id: RB-PAY-012
version: 2.0
title: Provider rate-limit cascade
services: payment, provider
type: runbook
trust: verified
---
# Provider rate-limit cascade

Honor Retry-After, cap exponential backoff, and keep the retry budget below the provider quota. A rollback is appropriate when the violating client behavior follows a deployment. Never bypass an external provider's limits.
