# Safety

The browser is never the security boundary. The API classifies every action as safe, sensitive, high risk or prohibited; checks target allow-lists; requires Incident Commander approval for sensitive actions; signs approvals with HMAC; deduplicates execution by idempotency key; and records audit events. Prohibited actions fail before simulation.

Only synthetic executors exist. An execution remains `EXECUTED` until post-action telemetry satisfies every recovery criterion for the configured number of windows. The public UI must label telemetry as synthetic and simulation values as estimates.
