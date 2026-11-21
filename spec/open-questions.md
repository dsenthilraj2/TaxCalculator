# Open Questions

Fill in **Answer** where you know it. Leave it blank or write "TBC — asking X" otherwise.
⭐ = blocks the workflow draft. Please answer these first.

## A. Product & business

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-01 | What is the product name: Taxcart, TSG Tax Gateway, something else? | Naming in the spec, code and portal | Taxcart |
| Q-02 ⭐ | Who pays TSG: the merchant (subscription), the provider (partner revenue share), or both? | Decides licensing, metering and billing workflows | Merchant / Client |
| Q-03 ⭐ | Whose provider account is used: the **merchant's own** Avalara/Zamp account, or a **TSG master account** that TSG resells? | Decides who owns the filing, how credentials are held, and whether tax reuse (W9) saves TSG money or the merchant's | Merchant's own for now|
| Q-04 | Is a licence check per call still needed (as in the MYOB design), or is "tenant active + within quota" enough? | Gateway pipeline step | License call per call is not needed |
| Q-05 | Pricing basis: per transaction, per tier, or flat? | Do we need usage metering and quotas? | Flat for now. Comparison with usage based would be good for proof |
| Q-06 | Which countries does the MVP cover: US sales tax only, or also UK VAT / EU IOSS / AU GST? | Provider choice (Zamp is US-only) and the data model (VAT numbers, reverse charge) | USA sales taxes only. Provider would be ZAMP for MVP |

## B. Source systems & triggers

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-10 ⭐ | Which **one or two** source systems are in the MVP? (Cin7 Core? MYOB Acumatica?) | Scope of the first build |CIN7 Omni and ZAMP|
| Q-11 ⭐ | Does tax need to be **in the ERP document before it's posted/sent to the customer** (real-time), or can it be filled in afterwards? | Decides trigger modes A/B/C (01-workflow §3) | Preferably before posting. Some ERPs have limitations, so will need to handle this based on the ERP |
| Q-12 | For each MVP source: can we install a customisation/plugin (like the MYOB button), does it have webhooks, or polling only? | Connector design | Needs to be assessed |
| Q-13 ⭐ | Does the gateway **write the tax back** into the ERP document (lines/total)? Can the ERP API accept an externally calculated tax amount? | Without write-back the gateway is reporting-only | Write back is critical. Some ERPs can accept API imputs for externally calculated amount. |
| Q-14 | Which document types per source: quote, sales order, invoice, credit note, POS sale? | W1–W4 coverage | Sales Order and Invoices for MVP. Others can follow. POS doesn't normally have such tax calculation complications |
| Q-15 | Which statuses trigger each action (e.g. Cin7 "Authorised" → estimate, "Invoiced" → commit)? | Status mapping config |Posted. Each ERP has a different action / status. This should be configurable per merchant/client by TSG consultants during onboarding |
| Q-16 | Where does the item's tax code live? Do merchants already have product tax codes, or do we need a mapping screen (SKU/category → provider tax code)? | W7, and correct calculation |Product tax code lives in ERP/source system, but may not be correct and requires validation on tax code and rates on every transaction. |
| Q-17 | Is the ship-from address always the warehouse on the line, or can there be drop-ship / multiple warehouses per order? | Line-level ship-from in the model | For MVP, the ship from will always be same for all line items |
| Q-18 | Expected volume per tenant (orders/day, peak) and number of tenants in year 1? | Sizing, polling frequency, cost |Volumes could vary. For MVP, the order volumes are about 40 to 50 orders per day |

## C. Users, portal & control

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-20 ⭐ | Who logs into the portal: TSG admins, merchant staff, **and/or the merchant's own customers** (Cin7 doc suggested end customers see their orders)? | Roles, security model, portal scope | TSG Admin, Merchant/Customer admin (transaction on view only mode)|
| Q-21 ⭐ | Who can **switch the tax provider**: only TSG admins, or merchant admins self-service? | W8 permissions and UI | TSG admin |
| Q-22 | When switching provider: immediately, from a chosen date, or only at the start of a filing period? | W8 rules |Chosen date |
| Q-23 | Can a tenant use **different providers per country/region** at the same time (e.g. Zamp for US, Taxually for UK)? | Routing logic |Yes, ZAMP for US, Taxually for UK, 1StopVAT for EU |
| Q-24 | Auth: is email + password enough, or do we need MFA / Microsoft / Google SSO? | Security doc | For MVP, email and password authentication |
| Q-25 | Should merchants be able to self-onboard (sign up, connect ERP, enter provider keys), or does TSG onboard everyone? | Onboarding workflow | No, TSG onboards clients|

## D. Tax behaviour

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-30 | Should address validation run automatically on every calculation, or only on demand? Should corrected addresses be written back to the ERP? | W5 | The three key elements on Sales tax calculation are Customer exemption certificate, Address validation and Tax calculation. These three elements should be validated / calculated on each call on each document. The first two can be asynchronous, if we can build that database in the server. |
| Q-31 | If the invoice tax differs from the order estimate, should we flag/alert it, or just use the invoice? | W2 | Tax values on Sales Quotes and Orders are estimates only. Invoice is what IRS looks for. So Sales Invoice is very important and all three elements should be recalculated. |
| Q-32 | Exemption: write the exempt flag back to the ERP customer (as in the Cin7 doc), or only apply it at calculation time? | W6 | Yes, possible on certain ERP systems |
| Q-33 | How are customers matched between the ERP and the provider (customer code, email, tax ID)? | W6, W7 | Customer Code and Tax ID |
| Q-34 | Multi-currency: do ERP documents come in non-USD currencies (the MYOB example was AUD) that need converting? Whose exchange rate? | Calculation inputs | For MVP and for most ERPs and customers, the currency will be USD for USA, EUR for Europe and GBP for UK.|
| Q-35 | If the provider is down, what should happen: block the ERP, return zero tax and recalculate later, or use the last known rate? | Failure workflow | Inform User with a message and Recalculate later. This can change with the product roadmap, where we can suggest Taxcart rates |

## E. Tax reuse / cost cutting (roadmap)

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-40 ⭐ | Is the goal to cut **TSG's** provider cost or the **merchant's**? (Depends on Q-03.) | Whether W9 is worth building | |
| Q-41 | Who files the tax returns: the provider (Avalara Returns / Zamp managed filing), the merchant, or TSG? If the provider files, invoices must still be committed, so reuse only saves on estimates. | W9 scope | |
| Q-42 | Can reuse be **shared across tenants** (same product tax code + same destination), or only within one tenant? | Bigger savings, but privacy and contract questions | |
| Q-43 | Have we checked Avalara/Zamp terms on caching or reusing their results? | Legal blocker | |
| Q-44 | How long can a reused rate be trusted (a day, a month, until the next rate-change date)? | Cache expiry | |
| Q-45 | Long term: should TSG own a rate table (e.g. a bought rate dataset) and only call providers for committing/filing? | Roadmap direction | |
| Q-46 | Who can change cache settings: only TSG admins, or tenant admins too (self-service in the portal)? | Permissions for W9.2 | |
| Q-47 | Suggested default TTL (proposal: 30 days, plus expire on 1 Jan/Apr/Jul/Oct)? Do we want a maximum TTL that tenants can't exceed? | Defaults in W9.2 | |
| Q-48 | On a verification mismatch, should the cache switch off automatically for that destination, or only alert? | REQ-CACHE-8 | |

## F. Configuration (02-configuration.md)

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-60 ⭐ | Which countries must onboarding support at launch (US, UK, EU, AU, NZ, ...)? | Country templates, capability matrix | |
| Q-61 | Who verifies the provider capability matrix (which provider is good for which country)? Will TSG certify each provider per country? | REQ-CFG-11 | |
| Q-62 | Can client admins create Tax Change Events for themselves, or only TSG? | §8 permissions | |
| Q-63 | For simple flat-rate countries (e.g. AU GST 10%), should the gateway calculate internally with no external calculator? | Big cost saving, but TSG takes on accuracy responsibility | |
| Q-64 | Do we have indicative per-call costs for Avalara, Zamp and Taxually to show savings? | Value dashboard (§9) | |
| Q-65 | Should a configuration change need approval (maker/checker), or is audit + rollback enough? | REQ-CFG-4 | |
| Q-66 | Must clients' notifications for tax events go by email, portal banner, or both? | §8 | |

## G. Calculation modes & roadmap (09-roadmap.md)

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-70 ⭐ | Is Improved priced differently from Live (cheaper, a savings share, or the same price with TSG keeping the margin)? | Sales story and who benefits from the TSG engine | |
| Q-71 | Will TSG ever answer **committed** invoices from its own engine (L4)? This needs legal/liability review and professional indemnity insurance. | Caps the roadmap at L3 if no | |
| Q-72 | Are the proposed eligibility rules acceptable (confidence lower bound ≥ 99.9%, ≥ 1,000 requests, ≥ 90 days, 30 days with no unexplained mismatch)? Is the match tolerance $0.01 / 0.01%? | Primary eligibility | |
| Q-73 ⭐ | Do provider contracts allow storing their results and comparing them with other engines (including publishing comparisons to clients)? | Legal blocker for parallel calculation | |
| Q-75 | Should a paid second provider run as a challenger? If yes, who pays for those extra calls: TSG, the client, or offered as an "assurance" add-on? | REQ-PAR-5 | |
| Q-76 | Can clients see engine comparisons for their own data, including provider vs provider? | Evidence dashboard, provider relationships | |
| Q-77 | Who does mismatch triage: a TSG tax analyst (in house), or a partner tax adviser? | Operating model for §3 | |
| Q-78 | How long must detailed engine results be kept (e.g. 7 years for audit, or 90 days detail + aggregates)? | Storage cost | |
| Q-74 | Which countries/regions should be the first candidates for the TSG engine? (Proposal: AU, NZ, US single-rate states.) | P3 scope | |

## H. Architecture (08-architecture.md)

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-80 | Are the proposed NFR targets acceptable (99.9% availability, ≤ 150 ms gateway overhead, 50 req/s)? Do clients need a contractual SLA? | Sizing, redundancy, cost | |
| Q-81 ⭐ | Which Azure region(s)? Do clients have data residency requirements (e.g. AU data stays in Australia East, US clients in US)? | Deployment topology, possibly one deployment per geography | |
| Q-82 | Is a single region (zone redundant) enough for the MVP, or is multi-region DR needed from day 1? | Cost and complexity | |
| Q-83 | Approve the ADRs in 08-architecture §13 (Python/FastAPI, MongoDB API, REST-first + CloudEvents, MUI, Terraform)? | Locks the stack | |
| Q-84 | Monthly Azure budget per environment for the MVP? | Service tiers (SQL pool size, Redis, Service Bus Premium) | |
| Q-85 | Is there an existing Azure subscription / Entra tenant at TSG, or do we create new ones? | Setup, billing | |
| Q-86 | Which ERP plugins must TSG build and host (e.g. an Acumatica customisation package for the Calculate Tax button)? Who maintains them per ERP version? | Connector delivery | |
| Q-87 | Do we need a public, documented API so third parties or clients can integrate directly (developer portal, SDKs)? | API management, versioning | |
| Q-88 ⭐ | The original spec required a **separate database per tenant**. Is pooled storage (shared collections, `tenantId` partition key, enforced in code) acceptable by default, with a dedicated database only for clients who need it? | Cost: a DB per tenant adds a fixed cost per client on a document DB | |
| Q-89 | Is Cosmos DB for MongoDB on Azure acceptable to start, or would you prefer MongoDB Atlas from day 1 (same everywhere, but a separate vendor bill)? | ADR-3 | |
| Q-90 | Does the real-time calculation (ERP button) tolerate occasional serverless cold starts in the MVP (a few seconds), or do we pay for always-ready instances from day 1? | S0 vs S1 cost | |

## I. Usage metering & billing (11-usage-metering.md)

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-91 | Should clients see **challenger** and TSG-engine call counts, or only requests and who responded? | Client usage screen (links to Q-76) | |
| Q-92 | Do we need hourly usage granularity, or is daily enough? | Counter storage | |
| Q-93 | (Later, billing) What is the billable unit: inbound request, document, committed invoice, or line? Are failed, duplicate or challenger calls ever billed? | Billable metric definition | |
| Q-94 | (Later, billing) Build our own rating/invoicing, or use a billing platform (Stripe Billing, Chargebee, Orb, Lago)? | Build vs buy | |
| Q-95 | Do we get usage statements from providers (Avalara/Zamp) in a format we can import for reconciliation? | Provider reconciliation screen | |

## J. Delivery

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-50 | Target date for MVP / first live client? (The Zamp deck said 8–12 weeks.) | Scope cut | |
| Q-51 | Do we have sandbox accounts for Avalara, Zamp and the MVP ERPs? | Build and test | |
| Q-52 | Team size and skills (.NET/React)? Is the stack in the 20 Nov spec fixed? | Architecture doc | |

## K. Follow-ups from the first answers (see [impact-analysis-01.md](impact-analysis-01.md))

| ID | Question | Why it matters | Answer |
|---|---|---|---|
| Q-100 ⭐ | Can the merchant admin edit anything (product tax setup, cache settings), or is the portal view-only for merchants in the MVP? (Raised by Q-15, Q-20, Q-25.) | Roles and which screens need edit modes | |
| Q-101 | Is a **TSG consultant** a separate role from TSG admin (e.g. can configure clients but can't change global settings or switch providers)? | Roles (Q-15, Q-21) | |
| Q-102 ⭐ | When the ERP's tax code differs from the client's product setup: use the ERP's code, use the setup's code, or hold the document for review? | Tax code validation (Q-16) | |
| Q-103 ⭐ | Is W3 (void a committed invoice) in the MVP? Without it, an invoice cancelled in Cin7 Omni may still be filed in Zamp. | MVP workflow scope (Q-14) | |
| Q-104 | Keep MFA for TSG admins in the MVP, even with email + password for merchants? TSG admins can see every client's data. | Security (Q-24) | |
| Q-105 ⭐ | Which Zamp capabilities do we use: calculation only, or also address validation and exemption certificates? If Zamp doesn't offer one, which provider does it? | Every-document checks (Q-30) | |
| Q-106 ⭐ | Does Cin7 Omni accept an externally calculated tax amount on sales orders and invoices through its API (line or document level)? Does it send webhooks, or must we poll? | Write-back and trigger mode (Q-12, Q-13) | |
| Q-107 | Who provides the Cin7 Omni and Zamp sandbox accounts for building and testing? (Links to Q-51.) | Build and test | |
| Q-108 | How often should stored addresses and exemption statuses be rechecked: on change only, daily, at certificate expiry? | Customer & address store (Q-30) | |
| Q-109 | Are these answers implied by Q-03 correct? Q-40: reuse cuts the **merchant's** cost. Q-41: Zamp files, using the merchant's account. Q-42: no sharing of results across tenants. | Cache roadmap (W9) | |
