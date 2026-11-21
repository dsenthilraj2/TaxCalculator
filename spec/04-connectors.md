# 04 — Source Connectors

**Status:** Draft v0.1 · **Date:** 2026-11-22 · **Owner:** TSG

A **source connector** connects Taxcart to one type of source system (ERP, finance or eCommerce app). It gets documents in, maps them to the canonical model, and writes tax back. The gateway core never contains source-specific code (01-workflow §2).

The MVP has **one connector: Cin7 Omni** (Q-10). This document defines the connector contract first, so later ERPs (MYOB Acumatica, Cin7 Core, Unleashed, Shopify, ...) plug in the same way.

---

## 1. What every connector does

| Step | Description |
|---|---|
| **Receive or fetch** | Gets documents by the trigger modes it supports (01-workflow §3): real-time call, webhook or polling |
| **Store raw** | Stores the native payload before anything else (REQ-WF-2) |
| **Filter by status** | Uses the client's status → action mapping (02-configuration §4.1). A status with no mapping is ignored |
| **Map** | Converts the native document to the canonical request: document type and version, customer (code, tax ID), ship-from, ship-to, lines with the ERP's tax code, freight, currency, date |
| **Write back** | Puts the tax into the ERP document (mandatory, REQ-WF-11). Where supported: corrected address, exempt flag, "tax pending" note |
| **Report** | Records each inbound document and each write-back in the transaction log and usage metering |

## 2. Connector capabilities

Each connector declares what it can do. Onboarding and the gateway use this declaration; nothing is assumed.

| Capability | Values | Answers |
|---|---|---|
| `triggerModes` | `REALTIME`, `WEBHOOK`, `POLLING` (one or more) | Q-11, Q-12 |
| `documentTypes` | `SALES_ORDER`, `INVOICE`, `QUOTE`, `CREDIT_NOTE` | Q-14 (MVP: order + invoice) |
| `acceptsExternalTax` | `LINE`, `DOCUMENT`, `NONE` | Q-13. `NONE` can't go live without an agreed workaround |
| `acceptsCustomerExemption` | yes / no | Q-32 |
| `acceptsAddressCorrection` | yes / no | Q-30 |
| `acceptsStatusNote` | yes / no: can show "tax pending" on the document | Q-35 |
| `customerKeys` | Which fields identify a customer: customer code, tax ID | Q-33 |
| `shipFromLevel` | `DOCUMENT` (MVP) or `LINE` | Q-17 |

> **REQ-CON-1** Every connector publishes its capabilities. Onboarding shows them, and only offers trigger modes and write-back options the connector supports.
> **REQ-CON-2** The onboarding readiness check (02-configuration §4, step 9) includes a **write-back test** against the client's ERP sandbox: create a test document, calculate, write back, read the document again and compare.
> **REQ-CON-3** A write-back the ERP rejects puts the transaction in *WriteBackFailed* (01-workflow §6). It's retried automatically and shown in the portal.
> **REQ-CON-4** Connectors are idempotent on (tenant, source system, document ID, document version, action) (REQ-WF-4). A webhook delivered twice or a document polled twice produces one calculation.
> **REQ-CON-5** Each client's connector credentials (ERP API keys or OAuth tokens) are stored in the secret store per tenant, never in configuration documents or logs.

## 3. Mapping

Field mapping is code inside each connector (one adapter per ERP type), tested against recorded sample payloads. Per-client differences are **configuration**, not code:

| Per-client setting | Example |
|---|---|
| Status → action mapping | Cin7 Omni invoice "Posted" → W2 commit (Q-15) |
| Which ERP field holds the product tax code | An item's tax code field, or a custom field (Q-16) |
| Customer key fields | Customer code + tax ID (Q-33) |
| Default ship-from | The client's warehouse (Q-17) |
| Polling interval (if polling) | Every 2 minutes |

> **REQ-CON-6** TSG consultants set the per-client mapping during onboarding (Q-15). Merchants view it.

## 4. Cin7 Omni (MVP)

**Status: needs a technical spike before build** (Q-12, Q-106, Q-107). The table below lists what must be confirmed against Cin7 Omni's API documentation and a sandbox account.

| Question | Why it matters | Fallback if the answer is no |
|---|---|---|
| Does Cin7 Omni send **webhooks** when a sales order or invoice is created or changes status? | Decides between event push (B) and polling (C) | Poll for changed documents every few minutes. At ~50 orders/day this is cheap (Q-18) |
| Can a **customisation or button** call Taxcart and wait for the answer? | Real-time mode (A) puts tax in the document before posting (Q-11) | Webhook or polling. Tax arrives seconds to minutes later |
| Can the API **write an externally calculated tax amount** onto order and invoice lines, or the document total? | Write-back is critical (Q-13) | Agree a workaround with TSG, e.g. a tax line item or a per-line tax rate override. Must be agreed before go-live |
| Can a document be **edited after it's posted** (for invoices)? | W2 runs on "Posted" (Q-15) | Calculate at an earlier status and commit at "Posted" |
| Which statuses exist for orders and invoices, and which mean void/cancelled? | Status mapping (§3) and W3 (Q-103) | — |
| Where do the **product tax code**, customer **tax ID** and customer **exemption** live? | Mapping (Q-16, Q-32, Q-33) | Custom fields |
| API **rate limits** and authentication method | Polling interval, retries, credential storage | — |

> **Note:** the Cin7 portal document in the original source material describes **Cin7 Core**, a different product with a different API. Its flows are input only and must be checked against Cin7 Omni.

**Spike output:** a short page added here with the confirmed answers, the chosen trigger mode, the write-back method, a recorded sample of each MVP document type (for tools/erp-sim), and an updated capability declaration (§2).

## 5. Testing

- **ERP simulator** (10-local-development §6): plays Cin7 Omni locally, including webhooks, polling, write-back and write-back rejections.
- **Contract tests** per connector: recorded payloads → canonical request, and canonical result → write-back call.
- **Sandbox test** at onboarding (REQ-CON-2).
