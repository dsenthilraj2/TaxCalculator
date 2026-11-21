# Tax Reference — Simple Countries

**Audience:** everyone (product, testers, sales, developers). **Not technical.**
**Status:** Draft v0.1 · **Date:** 2026-11-21

## Why this folder exists

The gateway needs a **simple, predictable tax calculator of its own** for the first version of the application. With one, we can test the whole system **at any time, without Avalara, Zamp or any other provider**:

- check that **login and the UI** work,
- send a **sample request** and check that the API answers,
- change a **setting** (provider, cache, tax event) and see the effect,
- run **demos** with believable numbers.

So this folder describes taxes that are **simple enough to calculate with confidence**: one national rate, or two or three rates with a few clear exceptions. Developers turn these pages into the simple TSG rules engine and the provider simulator. Testers use the [test scenarios](test-scenarios.md) as expected answers.

> ⚠️ **Not tax advice, and not for compliance.** These pages are simplified on purpose, for testing and demos. Rates and rules must be **verified against the official source** (linked on each page) before being used for anything real. Each page shows a "Last verified" date.

## Complexity levels

| Level | Description | Examples | In this folder? |
|---|---|---|---|
| **1 — Single rate** | One national rate. A few things are tax-free. | Australia, New Zealand, Singapore | ✅ |
| **2 — Few rates / simple exceptions** | Two or three rates chosen by product type. One level of government. | Japan (10% / 8%), United Kingdom (20% / 5% / 0%), US states with **no local tax** (Michigan, Indiana) | ✅ |
| **3 — Multi-level** | Federal + provincial/state + county/city. Rate depends on the exact address. | Canada (GST + PST/HST), most US states, Brazil, India | ❌ Use real providers |

## Country pages

| Country | Tax | Rates | Level | Page |
|---|---|---|---|---|
| Australia | GST | 10% | 1 | [australia.md](australia.md) |
| New Zealand | GST | 15% | 1 | [new-zealand.md](new-zealand.md) |
| Singapore | GST | 9% | 1 | [singapore.md](singapore.md) |
| Japan | Consumption tax | 10% / 8% | 2 | [japan.md](japan.md) |
| United Kingdom | VAT | 20% / 5% / 0% | 2 | [united-kingdom.md](united-kingdom.md) |
| United States: Michigan, Indiana | Sales tax | 6% · 7% (statewide, no local) | 2 | [us-simple-states.md](us-simple-states.md) |

## Plain-language glossary

| Term | Meaning |
|---|---|
| **GST / VAT / Consumption tax** | Tax added to the sale price at each step of the supply chain. Businesses get back the tax they paid on their purchases. Australia, New Zealand and Singapore call it GST, the UK calls it VAT, Japan calls it consumption tax. |
| **Sales tax (US)** | Tax charged only on the final sale to the end customer, set by each state (and often by cities/counties too). |
| **Standard rate** | The normal rate that applies unless a rule says otherwise. |
| **Reduced rate** | A lower rate for certain products (e.g. food in Japan, home energy in the UK). |
| **Zero-rated / GST-free** | Taxable, but at 0%. The seller still reports the sale and can reclaim tax on its costs. |
| **Exempt / input-taxed** | Outside the tax. No tax is charged, and the seller generally can't reclaim tax on related costs. *For our calculator the tax amount is also 0, but it's labelled differently.* |
| **Not taxable** | Not covered by the tax at all (e.g. most services under US sales tax). |
| **Tax-exclusive price** | The price before tax. Tax is added on top: `tax = price × rate`. |
| **Tax-inclusive price** | The price already includes tax. Tax is extracted: `tax = price × rate ÷ (1 + rate)`. In Australia that's 1/11 of the price. |
| **Export** | Goods sent to a customer outside the country. Usually 0% (zero-rated / GST-free) in the seller's country. |
| **Registration threshold** | The sales level above which a business must register and charge the tax |
| **Exemption certificate (US)** | A document from a customer (e.g. a reseller) that lets the seller not charge sales tax |

## Shared test product categories

To keep testing the same everywhere, every country page uses the **same small set of product categories**. Products in the demo data are mapped to one of these.

| Code | Category | Plain description |
|---|---|---|
| `TSG-GEN` | General goods | Everyday taxable goods: electronics, furniture, tools |
| `TSG-FOOD` | Basic food | Groceries for home: bread, milk, fruit, vegetables |
| `TSG-FOOD-PREP` | Prepared food / dining | Hot food, restaurant meals, catering |
| `TSG-ALC` | Alcohol | Beer, wine, spirits |
| `TSG-MED-RX` | Prescription medicine | Medicines dispensed on prescription |
| `TSG-EDU` | Education course | Tuition from a recognised education provider |
| `TSG-FIN` | Financial service | Loan interest, bank fees, insurance |
| `TSG-CLOTH-CHILD` | Children's clothing | Clothes and shoes for young children |
| `TSG-ENERGY-HOME` | Home energy | Electricity and gas for a household |
| `TSG-NEWS` | Newspaper subscription | Printed newspaper delivered regularly |
| `TSG-BOOK` | Books | Printed books |

### Treatment by country (summary)

| Code | 🇦🇺 AU | 🇳🇿 NZ | 🇸🇬 SG | 🇯🇵 JP | 🇬🇧 UK | 🇺🇸 MI | 🇺🇸 IN |
|---|---|---|---|---|---|---|---|
| `TSG-GEN` | 10% | 15% | 9% | 10% | 20% | 6% | 7% |
| `TSG-FOOD` | GST-free | 15% | 9% | **8%** | 0% | Exempt | Exempt |
| `TSG-FOOD-PREP` | 10% | 15% | 9% | 10% (dine-in) | 20% | 6% | 7% |
| `TSG-ALC` | 10% | 15% | 9% | 10% | 20% | 6% | 7% |
| `TSG-MED-RX` | GST-free | 15% | 9% | Exempt* | 0% | Exempt | Exempt |
| `TSG-EDU` | GST-free | 15% | 9% | Exempt* | Exempt* | Not taxable | Not taxable |
| `TSG-FIN` | Input-taxed | Exempt | Exempt | Exempt | Exempt | Not taxable | Not taxable |
| `TSG-CLOTH-CHILD` | 10% | 15% | 9% | 10% | 0% | 6% | 7% |
| `TSG-ENERGY-HOME` | 10% | 15% | 9% | 10% | **5%** | *verify* | *verify* |
| `TSG-NEWS` | 10% | 15% | 9% | **8%** | 0% | *verify* | *verify* |
| `TSG-BOOK` | 10% | 15% | 9% | 10% | 0% | 6% | 7% |

\* Only when conditions are met (e.g. insured medical care, an eligible education body). For testing, treat it as shown.
*verify* = not used in test scenarios until confirmed from the official source.

## Rules every simple calculator follows (version 1)

1. **Domestic sales:** apply the country's rate for the product category.
2. **Exports** (ship-to outside the seller's country): 0%, labelled "export / zero-rated". (US states: out of scope. Only in-state sales are tested.)
3. **Business customers in GST/VAT countries are still charged tax.** There's no exemption just for being a business. (Cross-border reverse charge is out of scope.)
4. **US only:** a customer with a valid **resale exemption certificate** is charged 0%.
5. **Rounding:** round tax **per line to 2 decimals, half-up** (Japan: **whole yen, round down, per rate per invoice**). The real rules allow other methods; these are simplified choices for testing.
6. **Inclusive prices:** extract the tax with `price × rate ÷ (1 + rate)`.
7. **Anything not covered** (imports, digital services from overseas, marketplace rules, special schemes): **out of scope**. Send it to a real provider.

## How the pages are used

| Who | Uses the pages to |
|---|---|
| Developers | Build the TSG rules engine and provider simulator rate tables (`tools/provider-sim/rates/*.yaml`) |
| Testers | Use [test-scenarios.md](test-scenarios.md) as expected results for manual and automated tests |
| Sales / demos | Show realistic calculations without any provider account |
| Product | Decide which countries could later be answered by the TSG engine (see [../09-roadmap.md](../09-roadmap.md)) |

> **Rule:** the YAML rate tables and test fixtures must match these pages. An automated test checks that every scenario in [test-scenarios.md](test-scenarios.md) gives the documented result.

## Page template (for adding a country)

Each country page has the same sections: **Summary card · What is taxed at which rate · Exceptions · How to calculate · Worked examples · Out of scope for v1 · Official sources · Last verified.**
