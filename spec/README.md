# TSG Tax Gateway — Specification

> Working name. Previously called "Taxcart" / "TSG Tax Calculator". To be confirmed (see Q-01).

## What this is

A multi-tenant **tax gateway**. It sits between finance/ERP/eCommerce systems, most of which can't calculate tax themselves, and external tax calculators (Avalara, Zamp, Taxually, ...).

It does two things:

1. **Connects.** It holds many connectors on both sides: source systems on one side, tax providers on the other.
2. **Bridges.** It receives a request from a client system, does the action (calculate, commit, void, validate address, check exemption), and returns the result.

A client can **switch tax provider at any time** without changing their ERP setup.

## Documents

| File | Purpose | Status |
|---|---|---|
| [01-workflow.md](01-workflow.md) | Core workflows: how a request flows through the gateway | Draft v0.1 |
| [open-questions.md](open-questions.md) | Questions to answer before the next draft | Open |
| [02-configuration.md](02-configuration.md) | Country-based onboarding, provider routing, cache config UI, tax change events, value dashboard | Draft v0.1 |
| 03-domain-model.md | Canonical entities (Tenant, Transaction, Line, Address, ...) | Not started |
| 04-connectors.md | Source connector framework and mapping | Not started |
| 05-providers.md | Tax provider adapter contract | Not started |
| 06-tenancy-security.md | Tenants, users, roles, auth, isolation | Not started |
| 07-portal-reporting.md | Customer portal and reports | Not started |
| [08-architecture.md](08-architecture.md) | Stack, code structure, database topology, Azure deployment, UI architecture, security, CI/CD, NFRs | Draft v0.1 |
| [09-roadmap.md](09-roadmap.md) | Parallel calculation (primary + challengers), comparison, evidence-based engine choice, phases | Draft v0.2 |

## Conventions

- Markdown + Mermaid diagrams (GitHub renders both).
- Requirements are tagged `REQ-<area>-<n>` so code, tests and tickets can refer to them.
- Open questions are tagged `Q-<n>` and are listed in [open-questions.md](open-questions.md).
- Source material: earlier TSG proposals (MYOBA–Avalara, Taxcart, Taxcart–Zamp, Cin7 portal, Tax Calculator Specs). They're kept outside the repo, in `document/`, which is git-ignored. They're input only; this spec doesn't have to follow them.
