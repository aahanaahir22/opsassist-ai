# Security model

OpsAssist AI is a portfolio simulator, not a production incident platform. It ships no production connectors or credentials. The API fails closed for unknown and prohibited actions, requires role-based signed approval for sensitive actions, accepts idempotency keys, redacts common secret patterns, blocks known prompt-injection phrases, records audit events, and prevents success confirmation before synthetic verification windows pass.

Do not send real customer telemetry, credentials, or confidential runbooks to the public demo. Report security issues privately to the repository owner rather than opening a public issue.
