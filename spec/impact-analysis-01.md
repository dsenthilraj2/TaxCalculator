# Impact Analysis 01: Answers to Open Questions (Sections A–D)

**Status:** Applied to the spec (v0.2 documents) · **Date:** 2026-11-22 · **Source:** [open-questions.md](open-questions.md), answered by SukeshNed (commits `06ed270`…`3aef47e` on `spec/initial-draft`)

27 questions are answered: Q-01–06, Q-10–18, Q-20–25, Q-30–35. Sections E–J (cache, configuration, calculation modes, architecture, metering, delivery) are still open.

This document lists what each answer changes in the spec and the code. The spec changes in §6 have been made; the code changes wait for the build slices in §5. The follow-up questions in §4 are now section K of open-questions.md.

---

## 1. Summary: what the MVP is now

| | Before (spec assumed) | Now (answers) |
|---|---|---|
| Product name | TSG Tax Gateway | **Taxcart** (Q-01) |
| Countries | Multi-country from day 1 | **US sales tax only** (Q-06) |
| Tax provider | Avalara + Zamp | **Zamp only** (Q-06, Q-10) |
| Source system | 1–2 ERPs (Cin7 Core? MYOB?) | **Cin7 Omni** (Q-10) |
| Documents | Quote, order, invoice, credit note, void | **Sales order + invoice** (Q-14) |
| Provider account | Open | **Merchant's own Zamp account** (Q-03) |
| Who pays | Open | **Merchant, flat fee** (Q-02, Q-05) |
| Portal users | TSG staff + client admin/user (+ end customers?) | **TSG admin + merchant admin with view-only transactions** (Q-20) |
| Onboarding | Self-service possible | **TSG onboards every client** (Q-25) |
| Each call | Calculate tax | **Exemption check + address validation + tax calculation, every document** (Q-30) |
| Write-back | Open | **Critical** (Q-13) |
| Volume | Open | **~40–50 orders/day per client** (Q-18) |

**The biggest effects:**
1. **Taxcart must check every document three ways.** The exemption certificate and address are checked on every call, not only on demand. The first two can run asynchronously against a server-side store of customers and addresses (Q-30). This is new, and the spec currently treats W5 and W6 as optional.
2. **The ERP's tax code is input to validate, not the truth** (Q-16). Our product → tax category setup becomes a *validation and correction* layer.
3. **Write-back to Cin7 Omni is now the main delivery risk.** It's critical (Q-13), but nobody has confirmed yet that Cin7 Omni accepts an externally calculated tax amount, or which trigger modes it supports (Q-12).
4. **Merchants mostly view.** TSG admins and consultants do all the configuration (Q-15, Q-21, Q-25). The current code lets client admins edit product setup.

---

## 2. Answer-by-answer impact

Impact: 🔴 changes design or scope · 🟠 changes a rule or screen · 🟢 confirms what we have, or naming only

### A. Product & business

| Q | Answer | Impact | Spec | Code |
|---|---|---|---|---|
| Q-01 | Taxcart | 🟢 | Rename "TSG Tax Gateway" → "Taxcart" in README, 01, 08, 10. | UI title, sign-in screen, app bar, OpenAPI title, dev IdP banner, package descriptions, READMEs (12 files outside the spec). **Recommendation:** keep the Python package `tsg_gateway` and the `TSG_` env prefix (internal names, a rename gives no value now). Rename only what users see. |
| Q-02 | Merchant pays | 🟢 | 11 §7: billing has a single payer (merchant). Remove "provider revenue share". | None. |
| Q-03 | Merchant's own provider account | 🔴 | **Credentials are per tenant** (Key Vault, per-tenant naming; already in 08 §9). **Implied answers:** cache savings (W9) go to the merchant, not TSG (Q-40). Sharing reuse across tenants (Q-42) is unlikely, since each merchant has a different account and contract. The filing owner is the merchant's Zamp account (Q-41). | Future `ProviderAccount` entity per tenant. Onboarding needs a "connect Zamp account" step with a test call (REQ-CFG-10). |
| Q-04 | No licence check per call | 🟢 | 01 §4 pipeline: "Check tenant active / licence / quota" → "Check tenant active". | Matches the code: we check that the tenant exists, with no licence call. |
| Q-05 | Flat pricing; compare with usage-based for proof | 🟠 | 11: metering stays (it's needed for the proof). Soft-limit alerts (11 §6) become optional. Add a **"what usage-based would have cost"** view to the value dashboard (02 §9) as the comparison. | Usage counters already exist. A comparison report comes later. |
| Q-06 | US sales tax only; Zamp | 🔴 | 02 §4 onboarding: country step fixed to US for MVP (keep the design, since Q-23 confirms more countries later). 02 §5 matrix: Zamp as the only MVP provider. 09 P1: "Avalara + Zamp adapters" → **Zamp adapter**. US detail now matters: state / county / city / special district, ZIP+4, origin vs destination states, nexus per state. | **Canonical `Address` is too thin for US** (only country/region/city/postal). Add `line1`, `line2`, `county`, ZIP+4. Result jurisdictions need state/county/city/special levels. The sample engine (AU/NZ/SG/JP/GB/US-MI/US-IN) stays as a **test** calculator, not an MVP feature. |

### B. Source systems & triggers

| Q | Answer | Impact | Spec | Code |
|---|---|---|---|---|
| Q-10 | Cin7 Omni (+ Zamp) | 🔴 | Zamp is the provider, so the **only MVP source is Cin7 Omni** (not Cin7 Core). The 04-connectors doc should start with Cin7 Omni. The Cin7 portal document we have describes Cin7 *Core*; check how much of it applies. | New Cin7 Omni connector + ERP simulator profile (tools/erp-sim). |
| Q-11 | Before posting preferred; depends on the ERP | 🟠 | Keep all three trigger modes (01 §3). Add a rule: **use the most real-time mode the ERP supports**. Record the chosen mode per client. | Connector declares supported modes (REQ-WF-1, already in spec). |
| Q-12 | Needs to be assessed | 🔴 | **Blocking spike:** does Cin7 Omni offer a customisation hook, webhooks or polling only? | — |
| Q-13 | Write-back critical; some ERPs accept external tax | 🔴 | Write-back becomes **mandatory** for an MVP connector. Add a connector capability `acceptsExternalTax` (line-level / document-level / none). **Blocking spike:** confirm Cin7 Omni can accept tax amounts through its API. If it can't, we need a fallback (e.g. a tax line item or a tax-rate override). | Connector port needs a `write_back` operation. Transaction states need a `WriteBackFailed` state. |
| Q-14 | Sales order + invoice for MVP | 🟠 | MVP workflows: **W1 (order estimate), W2 (invoice commit), W5, W6, W7**. W4 (credit note) moves after MVP. **Follow-up:** is W3 (void) in the MVP? If an invoice committed to Zamp is cancelled in Cin7 and we don't void it, it may still be filed. We recommend W3 in MVP. | — |
| Q-15 | "Posted" triggers; mapping per client by TSG consultants | 🟠 | Status mapping is per client, configured by TSG only (matches 02 §2 "Connector setup: TSG edit, client view"). Add a **status → action mapping screen** to the admin UI. | New config entity `StatusMapping` (tenant, source, document type, status, action). |
| Q-16 | Tax code lives in the ERP; may be wrong; validate every transaction | 🔴 | **Changes the product setup module's role.** The ERP sends a tax code on each line. Taxcart **validates** it against the client's product setup and flags mismatches. W7 becomes "keep the expected mapping current", not "be the only source". Add a **tax code exceptions** view (unknown product, code differs from setup, code not valid for Zamp). Also needs a map **TSG category ↔ Zamp product tax code**. | Today the resolver uses line → product → group → default, and the line code wins silently. Change: keep the ERP code as `source_tax_code`, compare it with the setup's code, and record `validation = match / mismatch / unknown` on each result. **Follow-up:** on a mismatch, which code is used: the ERP's, the setup's, or block for review? |
| Q-17 | One ship-from per document in MVP | 🟢 | Document-level ship-from (01 W1 inputs). Line-level ship-from goes to the roadmap. | Matches the code: `TaxRequest.ship_from` is already per document. |
| Q-18 | ~40–50 orders/day | 🟢 | Very small. Serverless consumption plan and serverless DB tier are enough (08 §7 stage S0). Even with ~4 provider calls per order (address, exemption, order, invoice), that's about 200 calls per day per client. Polling every 1–5 minutes is cheap. NFRs (Q-80) can be relaxed for MVP. | None. |

### C. Users, portal & control

| Q | Answer | Impact | Spec | Code |
|---|---|---|---|---|
| Q-20 | TSG admin; merchant admin with view-only transactions | 🔴 | No end-customer access. Roles for MVP: **TsgAdmin** (+ a TSG consultant/analyst role, see follow-up) and **merchant admin**. Update 02 §2 and 08 §9. **Follow-up:** "view-only" covers transactions. Can the merchant admin edit **anything** (product tax setup, cache)? Given Q-15/Q-21/Q-25, we assume **view-only everywhere** for MVP. | `ClientAdmin` can edit product setup today (`_SETUP_WRITERS`). If confirmed: make `ClientAdmin` read-only (one-line change plus tests), and drop `ClientUser` from the MVP personas, or keep it for later. |
| Q-21 | Only TSG admin switches provider | 🟢 | 01 W8 and 02 §2: provider per country is edited by TSG admins only. Client admins view. | Future screen, TSG-only. |
| Q-22 | Switch on a chosen date | 🟢 | Matches effective dating (REQ-CFG-3). W8 flow: replace "Immediately / From date" with **"Effective date (today or later)"**. | — |
| Q-23 | Yes: Zamp US, Taxually UK, 1StopVAT EU | 🟢 | Confirms per-country routing (02 §6). Add **1StopVAT** to the provider catalogue. Post-MVP. | — |
| Q-24 | Email + password for MVP | 🟠 | 08 §9 says "MFA required for admins". **Recommendation:** email + password for merchant users, but keep MFA for TSG admins, since they can see every client's data. Entra External ID supports both at no extra cost. **Follow-up:** confirm. | None. The dev IdP and OIDC code don't depend on how the user signs in. |
| Q-25 | TSG onboards every client | 🟠 | Onboarding wizard (02 §4) is **admin-only**. Remove self-service paths. | — |

### D. Tax behaviour

| Q | Answer | Impact | Spec | Code |
|---|---|---|---|---|
| Q-30 | Exemption + address + tax on every call, every document; the first two can be async with a server-side DB | 🔴 | W5 and W6 change from "on demand and/or" to **on every document**. New design: a **customer & address store** per tenant (validated address, exemption status, certificate expiry, last checked). The hot path reads the store. A background job refreshes entries when they change or go stale. If an entry is missing, check in line on first use. This is a new collection and a new background job, so a timer/queue trigger is needed in MVP (08 §6.2), not just REST. | New domain: `CustomerRecord`, `ValidatedAddress`. New ports: `AddressValidator`, `ExemptionChecker` (Zamp first). New collections. Canonical `Customer` needs `tax_id`, exemption certificate reference and expiry. |
| Q-31 | Order tax is an estimate; invoice is what counts; recalculate all three at invoice | 🟠 | W2: **always recalculate exemption, address and tax at invoice**. Never reuse the order's result. Strengthens REQ-CACHE-6: no cache for commits. Keep the order vs invoice difference as information in reports, not an alert. | — |
| Q-32 | Write exempt flag back: possible on some ERPs | 🟠 | Connector capability `acceptsCustomerExemption`. Write back where supported. | Connector port. |
| Q-33 | Match customers by customer code + tax ID | 🟠 | 03-domain-model: customer key = (tenant, source customer code), with tax ID as a second match. | Add `tax_id` to `Customer`. Index on (tenantId, customerCode). |
| Q-34 | USD for US, EUR for EU, GBP for UK; no conversion | 🟢 | No FX in MVP. Rule: **the document currency must match the country's currency**, otherwise reject. | Matches the code: the engine already rejects a currency that doesn't match the jurisdiction. |
| Q-35 | Provider down: tell the user and recalculate later. Roadmap: suggest Taxcart rates | 🟠 | Matches REQ-WF-5. Add: (a) a clear **user message** back to the ERP in real-time mode ("Tax could not be calculated, it will be retried"); (b) an **automatic retry** job, not only manual reprocessing; (c) a write-back that tells the user tax is pending in push/pull modes. The roadmap item "suggest Taxcart rates" links to the parallel engines (09): a proven cache or TSG-rules result could be offered as a fallback. | Needs the retry/outbox job (same background trigger as Q-30). New state `PendingRetry`. Today a provider failure just returns 503 `dependency-unavailable`. |

---

## 3. Effect on what's already built

| Area | Status | Change needed |
|---|---|---|
| Health API, logging, local stack, demo scripts | ✅ No change | — |
| OIDC sign-in, dev IdP, tenant isolation | ✅ Fits | Personas: add a TSG consultant (if a separate role), make the Acme admin read-only (Q-20). Rename the banner to Taxcart. |
| Product → tax category setup | 🟠 Repurpose | Becomes the **expected mapping** for validating the ERP's codes (Q-16). Add the Zamp product tax code to each TSG category. Edit rights: TSG only (Q-20). |
| Canonical model | 🟠 Extend | US address fields, customer tax ID and exemption certificate, US jurisdiction levels (Q-06, Q-30, Q-33). |
| Sample calculator (tsg_rules) | 🟢 Keep as test tool | Not an MVP feature (US-only, Zamp). Still useful for UI/API tests and as the future P3 challenger. Consider adding more US single-rate states for US-focused demos. |
| Usage metering | ✅ Fits | Q-05 keeps it, for proof. Later: a "usage-based price" comparison. |
| Dashboard / portal | 🟠 Adjust | Read-only merchant view. Add the tax code exceptions view (Q-16) and a failed/pending-retry list (Q-35). |

---

## 4. Follow-up questions raised by these answers

To add to open-questions.md as a new section K:

| ID | Question | From |
|---|---|---|
| Q-100 | Can the merchant admin edit anything (product tax setup, cache settings), or is the portal view-only for merchants in MVP? | Q-20, Q-15, Q-25 |
| Q-101 | Is a "TSG consultant" a separate role from TSG admin (e.g. can configure clients but not change global settings or switch providers)? | Q-15, Q-21 |
| Q-102 | When the ERP's tax code differs from the client's setup: use the ERP's code, use the setup's code, or block the document for review? | Q-16 |
| Q-103 | Is W3 (void a committed invoice) in the MVP? Without it, a cancelled invoice may stay filed in Zamp. | Q-14 |
| Q-104 | Keep MFA for TSG admins in MVP, even with email + password for merchants? | Q-24 |
| Q-105 | Which Zamp capabilities do we use: calculation only, or also address validation and exemption certificates? If Zamp doesn't do one, which provider does? | Q-06, Q-30 |
| Q-106 | Does Cin7 Omni accept an externally calculated tax amount on sales orders and invoices through its API (line level or document level)? Does it send webhooks? | Q-12, Q-13 |
| Q-107 | Who owns the Cin7 Omni and Zamp sandbox accounts we can use for building and testing? (Links to Q-51.) | Q-10 |
| Q-108 | How often should stored addresses and exemption statuses be rechecked (e.g. on change only, daily, at certificate expiry)? | Q-30 |
| Q-109 | Are the answers implied by Q-03 correct: Q-40 = cut the merchant's cost, Q-41 = Zamp files using the merchant's account, Q-42 = no sharing across tenants? | Q-03 |

---

## 5. Effect on the build plan

The next slices change. The provider simulator should focus on **Zamp**, not three providers.

| Order | Slice | Why now |
|---|---|---|
| 1 | **Spikes:** Cin7 Omni API (triggers, write-back) and Zamp API (calculate, commit, void, address, exemption) | Q-12/Q-13 are the biggest risks. Needs sandbox access (Q-107). |
| 2 | **US canonical model:** addresses, customers with tax ID and exemption, US jurisdiction levels | Everything after this depends on it |
| 3 | **Zamp simulator + Zamp adapter** (calculate, commit, void) | The only MVP provider. Simulator first so we can build without the sandbox |
| 4 | **Tax code validation** (Q-16) + read-only merchant role (Q-20) | Small changes to code that already exists |
| 5 | **Customer & address store** + background refresh + retry job (Q-30, Q-35) | Brings in the first background trigger |
| 6 | **Cin7 Omni connector + ERP simulator:** sales order → W1, posted invoice → W2, write-back | Depends on spike 1 |
| 7 | **Admin onboarding:** client, Zamp account, Cin7 connection, status mapping (Q-15, Q-25) | TSG-only screens |

Not changed by these answers: P2 (cache + parallel framework) and later. They wait for Q-40–48 and Q-70–78.

---

## 6. Spec documents to update once this is agreed

| Document | Changes |
|---|---|
| README.md, all docs | Product name → Taxcart |
| 01-workflow.md | Actors (no end customers; merchant view-only), pipeline (no licence/quota), W1/W2 every-document exemption + address, W2 always recalculates, W3 per Q-103, W4 post-MVP, W5/W6 every document with async store, W7 = validation, W8 effective date and TSG-only, provider-down behaviour, new states `PendingRetry` and `WriteBackFailed` |
| 02-configuration.md | §2 permission table (TSG-only edits, onboarding admin-only), §4 US-only MVP, §5 add 1StopVAT and Zamp as the MVP provider, status mapping screen |
| 08-architecture.md | §6: a background trigger in MVP (refresh + retry), §9 roles and MFA (Q-104), §12 NFRs sized for ~50 orders/day |
| 09-roadmap.md | P1 = Cin7 Omni + Zamp, US only, W1/W2/W5/W6/W7 (+W3); "suggest Taxcart rates when the provider is down" as a P4 benefit |
| 10-local-development.md | Personas (Q-20/Q-101), provider simulator: Zamp first |
| 11-usage-metering.md | Flat pricing; usage-based comparison for proof |
| tax-reference/ | Add a US reference for the MVP: state/county/city/special levels, origin vs destination states, exemption certificates, nexus |
| New: 04-connectors.md | Cin7 Omni first, with connector capabilities (`triggerModes`, `acceptsExternalTax`, `acceptsCustomerExemption`) |
