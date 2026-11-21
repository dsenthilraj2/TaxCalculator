# Taxcart — Specification

> Product name confirmed as **Taxcart** (Q-01). Internal code names (the `tsg_gateway` Python package, `TSG_` settings) stay as they are.

**MVP:** US sales tax only, **Cin7 Omni → Zamp**, sales orders and invoices, onboarded and configured by TSG, read-only portal for merchants. See [impact-analysis-01.md](impact-analysis-01.md) for how the first answers shaped this.

## What this is

A multi-tenant **tax gateway**. It sits between finance/ERP/eCommerce systems, most of which can't calculate tax themselves, and external tax calculators (Avalara, Zamp, Taxually, ...).

It does two things:

1. **Connects.** It holds many connectors on both sides: source systems on one side, tax providers on the other.
2. **Bridges.** It receives a request from a client system, does the action (calculate, commit, void, validate address, check exemption), and returns the result.

A client can **switch tax provider at any time** without changing their ERP setup.

## Documents

| File | Purpose | Status |
|---|---|---|
| [01-workflow.md](01-workflow.md) | Core workflows: how a request flows through Taxcart, the three checks on every document, provider-down behaviour | Draft v0.2 |
| [tax-reference/](tax-reference/README.md) | **Non-technical.** US sales tax overview for the MVP, simple-country tax pages (AU, NZ, SG, JP, UK, US MI/IN), shared test product categories, test scenarios with expected answers | Draft v0.2 |
| [open-questions.md](open-questions.md) | Questions to answer before the next draft. A–D answered; K holds follow-ups | Partly answered |
| [impact-analysis-01.md](impact-analysis-01.md) | What the answers to Q-01–35 change in the spec and code | Applied to the spec (v0.2) |
| [02-configuration.md](02-configuration.md) | Country-based onboarding (TSG-run), permissions, status mapping, tax code validation policy, provider routing, cache config UI, tax change events, value dashboard | Draft v0.2 |
| 03-domain-model.md | Canonical entities (Tenant, Transaction, Line, Address, Customer, ...) | Not started |
| [04-connectors.md](04-connectors.md) | Source connector contract and capabilities, Cin7 Omni (MVP) spike checklist | Draft v0.1 |
| 05-providers.md | Tax provider adapter contract | Not started |
| 06-tenancy-security.md | Tenants, users, roles, auth, isolation | Not started |
| 07-portal-reporting.md | Customer portal and reports | Not started |
| [08-architecture.md](08-architecture.md) | Python hexagonal architecture, document DB (MongoDB API), REST → queue evolution, background jobs in the MVP, serverless-first multi-cloud roadmap, React UI, Python standards | Draft v0.3 |
| [09-roadmap.md](09-roadmap.md) | Parallel calculation (primary + challengers), comparison, evidence-based engine choice, phases | Draft v0.3 |
| [10-local-development.md](10-local-development.md) | Cloud-free local stack (local MongoDB), dev identity provider with personas, provider simulator (Zamp first), ERP simulator (Cin7 Omni first), test levels, seed data | Draft v0.2 |
| [11-usage-metering.md](11-usage-metering.md) | Requests per client, calls per calculator, who responded, usage screens; flat pricing now, billing models kept as roadmap | Draft v0.2 |


## Conventions

- Markdown + Mermaid diagrams (GitHub renders both).
- Requirements are tagged `REQ-<area>-<n>` so code, tests and tickets can refer to them.
- Open questions are tagged `Q-<n>` and are listed in [open-questions.md](open-questions.md).
- Source material: earlier TSG proposals (MYOBA–Avalara, Taxcart, Taxcart–Zamp, Cin7 portal, Tax Calculator Specs). They're kept outside the repo, in `document/`, which is git-ignored. They're input only; this spec doesn't have to follow them.
