# Test Scenarios

**Audience:** testers, developers, demos · **Status:** Draft v0.1 · [Back to index](README.md)

Ready-made scenarios with **known correct answers**, based on the simple countries in this folder. Use them any time to check that the application works: login, the UI, the API, settings. You don't need a real tax provider.

- **Part A — Tax scenarios:** inputs and the exact expected tax.
- **Part B — System checks:** quick checks of login, the API, settings and usage. They reuse Part A.

All amounts are **tax-exclusive** unless the scenario says "incl". Rounding follows the [simple calculator rules](README.md#rules-every-simple-calculator-follows-version-1).
Test users (personas) and demo clients (Acme, Beta) are defined in [../10-local-development.md](../10-local-development.md) §4.2 and §8.

---

## Part A — Tax scenarios

### Australia (GST 10%), seller in Sydney

| ID | What it tests | Lines | Ship-to | Expected tax | Expected total |
|---|---|---|---|---|---|
| AU-01 | Basic 10% | `TSG-GEN` 100.00 | Melbourne, AU | **10.00** | 110.00 |
| AU-02 | Inclusive price | `TSG-GEN` 110.00 incl | Melbourne, AU | **10.00** | 110.00 |
| AU-03 | Mixed basket (GST-free food) | `TSG-GEN` 50.00 + `TSG-FOOD` 20.00 | Brisbane, AU | **5.00** | 75.00 |
| AU-04 | Export is GST-free | `TSG-GEN` 200.00 | Auckland, NZ | **0.00** (export) | 200.00 |
| AU-05 | Rounding (exclusive) | `TSG-GEN` qty 3 × 3.33 = 9.99 | Perth, AU | **1.00** (0.999 → 1.00) | 10.99 |
| AU-06 | Rounding (inclusive) | `TSG-GEN` 9.99 incl | Perth, AU | **0.91** (0.908 → 0.91) | 9.99 |
| AU-07 | Food exception | `TSG-FOOD-PREP` 30.00 | Sydney, AU | **3.00** | 33.00 |
| AU-08 | Input-taxed financial | `TSG-FIN` 100.00 | Sydney, AU | **0.00** (input-taxed) | 100.00 |

### New Zealand (GST 15%)

| ID | What it tests | Lines | Expected tax | Expected total |
|---|---|---|---|---|
| NZ-01 | Basic 15% | `TSG-GEN` 200.00 | **30.00** | 230.00 |
| NZ-02 | Inclusive price | `TSG-GEN` 230.00 incl | **30.00** | 230.00 |
| NZ-03 | No food exemption | `TSG-FOOD` 40.00 | **6.00** | 46.00 |
| NZ-04 | Exempt financial | `TSG-FIN` 100.00 | **0.00** (exempt) | 100.00 |

### Singapore (GST 9%)

| ID | What it tests | Lines | Expected tax | Expected total |
|---|---|---|---|---|
| SG-01 | Basic 9% | `TSG-GEN` 100.00 | **9.00** | 109.00 |
| SG-02 | Inclusive price | `TSG-GEN` 109.00 incl | **9.00** | 109.00 |
| SG-03 | Exempt financial | `TSG-FIN` 100.00 | **0.00** (exempt) | 100.00 |

### Japan (10% / 8%, whole yen, round down per rate)

| ID | What it tests | Lines | Expected tax | Expected total |
|---|---|---|---|---|
| JP-01 | Standard 10% | `TSG-GEN` ¥1,000 | **¥100** | ¥1,100 |
| JP-02 | Reduced 8% | `TSG-FOOD` ¥1,000 | **¥80** | ¥1,080 |
| JP-03 | Two rates on one invoice | `TSG-GEN` ¥1,000 + `TSG-FOOD` ¥1,000 | **¥180** (100 + 80) | ¥2,180 |
| JP-04 | Round down | `TSG-FOOD` ¥1,234 | **¥98** (98.72 → 98) | ¥1,332 |
| JP-05 | Dine-in vs takeaway | `TSG-FOOD-PREP` ¥2,000 | **¥200** (10%) | ¥2,200 |

### United Kingdom (VAT 20% / 5% / 0%)

| ID | What it tests | Lines | Expected tax | Expected total |
|---|---|---|---|---|
| UK-01 | Standard 20% | `TSG-GEN` 100.00 | **20.00** | 120.00 |
| UK-02 | Reduced 5% | `TSG-ENERGY-HOME` 100.00 | **5.00** | 105.00 |
| UK-03 | Zero-rated | `TSG-CLOTH-CHILD` 100.00 | **0.00** (zero-rated) | 100.00 |
| UK-04 | Three rates on one invoice | `TSG-GEN` 100.00 + `TSG-CLOTH-CHILD` 40.00 + `TSG-ENERGY-HOME` 60.00 | **23.00** (20 + 0 + 3) | 223.00 |
| UK-05 | Inclusive price | `TSG-GEN` 120.00 incl | **20.00** | 120.00 |
| UK-06 | Exempt vs zero-rated label | `TSG-FIN` 100.00 | **0.00** (exempt, *not* zero-rated) | 100.00 |

### United States: Michigan (6%) and Indiana (7%)

| ID | What it tests | Customer | Lines | Ship-to | Expected tax | Expected total |
|---|---|---|---|---|---|---|
| MI-01 | Statewide rate | Consumer | `TSG-GEN` 100.00 | Detroit, MI | **6.00** | 106.00 |
| MI-02 | Grocery exemption | Consumer | `TSG-FOOD` 50.00 | Lansing, MI | **0.00** | 50.00 |
| MI-03 | Mixed basket | Consumer | `TSG-GEN` 100.00 + `TSG-FOOD` 50.00 | Grand Rapids, MI | **6.00** | 156.00 |
| MI-04 | Same rate anywhere in the state | Consumer | `TSG-GEN` 100.00 | Marquette, MI | **6.00** | 106.00 |
| IN-01 | Statewide rate | Consumer | `TSG-GEN` 100.00 | Indianapolis, IN | **7.00** | 107.00 |
| IN-02 | Resale exemption certificate | Reseller (valid cert) | `TSG-GEN` 500.00 | Fort Wayne, IN | **0.00** (exempt customer) | 500.00 |
| IN-03 | Prescription exemption | Consumer | `TSG-MED-RX` 80.00 | Bloomington, IN | **0.00** | 80.00 |
| IN-04 | Rounding | Consumer | `TSG-GEN` 0.99 | Indianapolis, IN | **0.07** (0.0693 → 0.07) | 1.06 |

### Negative scenarios (the request should be rejected or flagged)

| ID | What it tests | Input | Expected result |
|---|---|---|---|
| NEG-01 | Unsupported country for the simple engine | Ship-to Toronto, CA | Not handled by the TSG engine → routed to a real provider, or a clear "country not supported" error |
| NEG-02 | Unknown product category | Line with code `TSG-UNKNOWN` | Validation error naming the line |
| NEG-03 | Negative amount on a sale | `TSG-GEN` −10.00 on an invoice | Validation error (refunds use the refund action) |
| NEG-04 | Currency mismatch | AU sale in USD | Validation error (or conversion, if configured later) |
| NEG-05 | Missing ship-to address | No address | Validation error |
| NEG-06 | US state with local taxes | Ship-to Denver, CO | Not handled by the TSG engine (Level 3) → provider |

---

## Part B — System checks (quick smoke tests)

Run these after any deployment, or locally with `make dev` + `make seed`.

| ID | Area | Steps | Expected |
|---|---|---|---|
| SYS-01 | Login | Log in as each test user (TSG admin, TSG analyst, Acme admin, Acme user, Beta admin) | Each lands on the right home page with the right menus |
| SYS-02 | Login rejection | Log in as the disabled user | Access refused with a clear message |
| SYS-03 | Tenant isolation | Beta admin opens Transactions | Sees **no** Acme transactions |
| SYS-04 | API is alive | `GET /health` | `200 OK` |
| SYS-05 | API calculate | Send **AU-01** with the Acme API key | `200`, tax **10.00**, `respondedBy` shown |
| SYS-06 | API auth | Send AU-01 with no or an invalid API key | `401` with a problem-details body |
| SYS-07 | Idempotency | Send AU-01 twice with the same `Idempotency-Key` | Same response. Usage counts 1 success + 1 duplicate. |
| SYS-08 | Portal shows result | After SYS-05, Acme admin opens Transactions | The transaction appears with tax 10.00 |
| SYS-09 | Switch calculator (setting) | Acme admin/TSG admin changes AU from `sim-avalara` to `tsg-rules`, then sends AU-03 | Tax **5.00**. `respondedBy` = `tsg-rules`. |
| SYS-10 | Parallel calculation | With a challenger enabled, send UK-04 | Primary answers 23.00. A challenger run and a comparison are recorded. |
| SYS-11 | Engine disagreement | Configure the simulator so `sim-zamp` differs for UK `TSG-ENERGY-HOME`, then send UK-02 | A mismatch shows in the evidence/triage screen |
| SYS-12 | Cache setting | Turn the cache on for AU, send AU-01 twice | The second response is served from the cache (`source = CACHE`). Tax still 10.00. |
| SYS-13 | Tax change event | Create an event for AU (force live), send AU-01 | Served live, not from the cache. The event is visible on the dashboard. |
| SYS-14 | Lock | TSG admin locks the cache OFF for UK. Acme admin tries to turn it on. | Blocked. Padlock and reason shown. |
| SYS-15 | Usage | After SYS-05 to SYS-13, open Usage | Request counts per calculator match the calls made |
| SYS-16 | Provider fault | Simulator: `sim-avalara` timeout 100%, send AU-01 | Retries, then fallback or a failed transaction per the fallback setting. Shows in the Failed list. |
| SYS-17 | Reprocess | Clear the fault, reprocess the failed transaction from the portal | Succeeds, tax 10.00 |
| SYS-18 | Audit | Open the audit log after SYS-09/12/14 | Each setting change is listed with who, when and the old/new value |

---

## Keeping this up to date

- Every Part A scenario also exists as a machine-readable fixture (`backend/tests/fixtures/scenarios/*.yaml`). An automated test runs all of them against the TSG rules engine and the provider simulator.
- If a rate changes: update the country page → update the scenarios here → update the YAML. The automated test fails until all three match.
