# Security model

OpsAssist AI is a portfolio simulator, not a production incident platform. It ships no production remediation connectors or credentials. The production profile validates Auth0 RS256 tokens against JWKS, requires an Organization tenant claim, enforces endpoint permissions, scopes persisted records by tenant, applies Redis-backed rate limits, and fails startup when required production configuration is incomplete. The policy layer fails closed for unknown and prohibited actions, verifies signed approvals, accepts tenant-scoped idempotency keys, redacts common secret patterns, blocks known prompt-injection phrases, records audit events, and prevents success confirmation before synthetic verification windows pass.

Do not send real customer telemetry, credentials, or confidential runbooks to the public demo. Report security issues privately to the repository owner rather than opening a public issue.
