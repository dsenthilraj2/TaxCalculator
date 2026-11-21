# Local-only tools

These are never packaged or deployed (spec/10-local-development.md, REQ-DEV-1). Each is built in a later slice.

| Folder | Purpose |
|---|---|
| `dev-idp/` | Local OIDC identity provider with test personas (**built**: `make idp`, `make token`) |
| `provider-sim/` | Tax provider simulator (rate tables from `spec/tax-reference/`) |
| `erp-sim/` | ERP simulator CLI (real-time, webhook, polling, write-back) |
| `api-collection/` | Bruno/Postman collection for the API |
