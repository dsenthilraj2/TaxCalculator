# 🇺🇸 United States — Sales Tax Overview (MVP)

**Level 3 (state + county + city + special districts)** · Last verified: *pending, verify before use* · [Back to index](README.md)

The Taxcart MVP covers **US sales tax only** (Q-06), calculated by **Zamp**. Taxcart doesn't calculate US tax itself in the MVP: Zamp does. This page explains, in plain language, what Taxcart has to get right **around** the calculation, so the team can design screens and tests and talk to clients.

For predictable test numbers, use the two states with a single statewide rate: [us-simple-states.md](us-simple-states.md) (Michigan, Indiana).

> ⚠️ **Not tax advice.** Simplified for product design and testing. Rates, thresholds and rules change and differ by state. Verify against each state's revenue department before relying on anything here.

## The big picture

- There's **no national (federal) sales tax**. Each state sets its own.
- **45 states and Washington DC** have a statewide sales tax. **Alaska, Delaware, Montana, New Hampshire and Oregon** don't, although some Alaska towns charge local sales tax.
- In most states, **counties, cities and special districts** (transit, stadium, school) add their own rate on top. The rate a customer pays is the **combined rate** for their exact address.
- The US has thousands of separate tax jurisdictions, and local rates change several times a year, usually at the start of a quarter.

## The three checks on every document (Q-30)

TSG's tax specialist named three things that decide whether US sales tax is right. Taxcart checks all three on every sales order and invoice.

### 1. Where is it going? (address validation)

- The **ship-to address** decides which jurisdictions apply.
- A **5-digit ZIP code isn't enough.** One ZIP code can cover several cities or districts with different rates. The full street address (or ZIP+4) is needed.
- Address validation corrects the address (spelling, ZIP+4) and finds its jurisdictions. A wrong address means the wrong rate.

### 2. Is the customer exempt? (exemption certificates)

- Some buyers don't pay sales tax: **resellers** (they'll charge tax when they resell), **nonprofits**, **government bodies**, and some **manufacturers** for qualifying purchases.
- The buyer gives the seller an **exemption certificate**. The seller must keep a valid one. If it's missing or expired, the seller is liable for the tax.
- Certificates are usually **per state**, and some expire (the rules vary by state). Taxcart tracks each customer's exemption status and certificate expiry date; it doesn't store the certificate itself.
- Customers are matched between the ERP and the provider by **customer code**, then **tax ID** (Q-33).

### 3. How much tax? (calculation)

Zamp calculates the tax from the address, customer, products, freight and date. Things that make it complicated:

| Topic | Plain explanation |
|---|---|
| **Product taxability** | Each state decides what's taxed. Groceries are often exempt or taxed at a lower rate. Clothing is exempt in a few states, and some exempt it only under a price limit. Software and digital goods vary widely. This is why the **product tax code** on each line matters. |
| **Freight / shipping** | Some states tax shipping charges, others don't, and some only when shipping is part of the sale price. |
| **Origin vs destination** | For sales within a state, a few states charge the rate where the **seller** is (origin-based). Most charge the rate where the **buyer** is (destination-based). Interstate sales are generally destination-based. |
| **Rate changes** | Local rates change often, usually on 1 January, 1 April, 1 July or 1 October. |

## When does a seller have to collect? (nexus)

- A seller must collect a state's sales tax only if it has **nexus** there.
- **Physical nexus:** an office, warehouse, staff or stock in the state.
- **Economic nexus:** since the 2018 Supreme Court decision *South Dakota v. Wayfair*, states can require out-of-state sellers to collect once their sales into the state pass a threshold, commonly **$100,000 a year** (some states also count the number of transactions; verify per state).
- **Marketplace facilitators** (e.g. Amazon) usually collect tax for sales made through them.

The provider normally knows the client's registrations. Taxcart records which states each client is registered in during onboarding (02-configuration §4).

## Orders versus invoices (Q-31)

- Tax on a **sales order** (or quote) is an **estimate**. Nothing is reported.
- The **invoice** is what tax authorities look at. At invoice time, Taxcart redoes all three checks and records (commits) the transaction with Zamp, which uses it for filing.
- If the invoice tax differs from the order estimate, the invoice is right.

## Test situations for the MVP

These test Taxcart's behaviour, not tax rates. Expected numbers for simple cases are in [test-scenarios.md](test-scenarios.md) (US-MI, US-IN).

| ID | Situation | Expected behaviour |
|---|---|---|
| US-SYS-01 | Exempt customer (resale) with a valid certificate for the ship-to state | No tax. The result says the exemption came from the customer store. |
| US-SYS-02 | Same customer, but the certificate expired yesterday | Taxed normally. The exception is listed so the merchant can collect a new certificate. |
| US-SYS-03 | Ship-to address with a 5-digit ZIP that spans two jurisdictions | Address validation resolves the full address before calculation. Never calculated on the ZIP alone. |
| US-SYS-04 | Address that can't be validated | The document isn't calculated on a guess. The user is told, and the document shows in the portal. |
| US-SYS-05 | Line whose ERP tax code differs from the client's product setup | Tax code exception recorded. Which code is used follows the client's policy (Q-102). |
| US-SYS-06 | Zamp unavailable when an invoice is posted | No zero tax. The user is told, the document is retried automatically, and tax is written back when it succeeds (Q-35). |
| US-SYS-07 | Order estimated, then invoiced with a changed quantity | Invoice recalculated from scratch. The invoice amount is written back and committed. |
| US-SYS-08 | Invoice in a currency other than USD | Rejected (Q-34). |
| US-SYS-09 | Ship-to in a state where the client isn't registered | Zero tax with the reason "not registered" (02-configuration §4). |

## Official sources

- Each state's department of revenue (rates, taxability, certificates).
- Streamlined Sales Tax Governing Board (member states, uniform rules and certificates): streamlinedsalestax.org
