# Security policy

## Supported scope

This repository is a portfolio prototype and not a production incident-response product. Do not connect the simulator to real infrastructure without an independent security review.

## Reporting

Report security issues privately to `aahanaahir10@gmail.com`. Do not open a public issue containing credentials, internal logs, personal data, or an exploitable proof of concept.

## Safe extension requirements

- Keep infrastructure actions behind a strict allow-list.
- Bind approvals to actor, action, target, expiry, and policy version.
- Use least-privilege, short-lived credentials from a secret manager.
- Strip secrets and personal data from telemetry and retrieved evidence.
- Make audit storage append-only and independently integrity-checked.
- Add authentication, authorization, rate limits, and tenant isolation.
- Confirm post-action state through a separate read path.

