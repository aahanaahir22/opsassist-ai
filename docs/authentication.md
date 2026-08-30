# Auth0 authentication and tenant isolation

OpsAssist uses an Auth0 Single Page Application for Universal Login and an Auth0 API for access tokens. Auth0 Organizations are mandatory in the production profile; the token's `org_id` claim becomes the tenant ID.

## Auth0 resources

1. Create an API with audience `https://api.opsassist.ai` and RS256 signing.
2. Create a Single Page Application and allow the deployed Site URL in callback, logout and web-origin settings.
3. Enable Organizations for the application and require organization selection/invitation.
4. Add API permissions: `incidents:read`, `incidents:write`, `actions:simulate`, `actions:approve`, `actions:execute`, `actions:verify`, `knowledge:read`, `knowledge:write`, `telemetry:write`, `evaluations:read`, `audit:read`, and `postmortems:write`.
5. Add roles such as `operator`, `incident_commander` and `admin`. Use an Auth0 Action to add role names to `https://opsassist.ai/roles`.

Frontend variables are `NEXT_PUBLIC_AUTH0_DOMAIN`, `NEXT_PUBLIC_AUTH0_CLIENT_ID` and `NEXT_PUBLIC_AUTH0_AUDIENCE`. API variables are `OPSASSIST_AUTH0_DOMAIN`, `OPSASSIST_AUTH0_AUDIENCE` and `OPSASSIST_AUTH_REQUIRED=true`.

The API never trusts actor IDs or roles submitted in an approval body. It derives the actor and role from the verified token, checks endpoint permissions, binds all workflow queries to `org_id`, and signs the approval record. Missing organizations, missing permissions, invalid signatures and expired tokens fail at the backend.

The unauthenticated public portfolio profile is enabled only with `OPSASSIST_AUTH_REQUIRED=false` and is labelled as a synthetic demo. It must not receive confidential telemetry or runbooks.
