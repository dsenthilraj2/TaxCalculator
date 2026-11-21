# 🇺🇸 United States — Simple States (Michigan, Indiana)

**Level 2 (one statewide rate + product exceptions)** · Last verified: *pending, verify before use* · [Back to index](README.md)

## Why these two states

Most US states let counties and cities add their own sales tax, so the rate depends on the exact street address (Level 3). **Michigan and Indiana have one statewide rate and no local sales tax**, so every address in the state gets the same rate. That makes them good test cases for US behaviour, especially **customer exemption certificates**, without needing address-level data.

(Other states without local sales tax, such as Kentucky, Rhode Island, Connecticut and Maine, could be added later the same way.)

## Summary cards

| Item | Michigan (MI) | Indiana (IN) |
|---|---|---|
| Tax | State sales tax | State sales tax ("gross retail tax") |
| Authority | Michigan Department of Treasury | Indiana Department of Revenue |
| Rate | **6%** | **7%** |
| Local sales tax | None | None |
| Currency | USD, 2 decimals | USD, 2 decimals |
| Price display | **Tax-exclusive** (tax added at checkout) | **Tax-exclusive** |
| Seller must collect if | Economic nexus: about $100,000 of sales into the state (verify) | Economic nexus: about $100,000 of sales into the state (verify) |

## What is taxed

| Category | Michigan | Indiana |
|---|---|---|
| General goods (`TSG-GEN`) | **6%** | **7%** |
| Groceries for home (`TSG-FOOD`) | **Exempt** | **Exempt** |
| Prepared food, restaurant meals (`TSG-FOOD-PREP`) | **6%** | **7%** |
| Alcohol (`TSG-ALC`) | **6%** | **7%** |
| Prescription medicine (`TSG-MED-RX`) | **Exempt** | **Exempt** |
| Services such as education and finance (`TSG-EDU`, `TSG-FIN`) | **Not taxable** | **Not taxable** |
| Home energy, newspapers | *Verify (special rules)* | *Verify (special rules)* |

## Customer exemptions (key US feature)

Unlike GST/VAT, US sales tax is only charged to the **final consumer**. These customers can buy **tax-free** if they give the seller a valid exemption certificate:

| Exemption reason | Example |
|---|---|
| **Resale** | A shop buying stock to resell |
| Non-profit / charity | Qualifying organisations (state rules apply) |
| Government | Federal or state agencies |
| Manufacturing / agriculture | Certain inputs used in production |

For testing: a customer flagged `RESALE` with a valid certificate is charged **0%** on all categories.

## How to calculate

- `tax = price × state rate` for taxable categories. 0 for exempt or not-taxable categories, or exempt customers.
- Round per line to the cent, half-up (simplified).
- Only **in-state** deliveries are tested (ship-to address in MI or IN).

## Worked examples

| # | Situation | Calculation | Tax | Total |
|---|---|---|---|---|
| 1 | MI: monitor $100.00 | 100.00 × 6% | **$6.00** | $106.00 |
| 2 | MI: groceries $50.00 | Exempt | **$0.00** | $50.00 |
| 3 | IN: monitor $100.00 | 100.00 × 7% | **$7.00** | $107.00 |
| 4 | IN: monitors $500.00 to a reseller with a certificate | Exempt customer | **$0.00** | $500.00 |
| 5 | MI: monitor $100.00 + groceries $50.00 | 6.00 + 0.00 | **$6.00** | $156.00 |

## Out of scope for v1

Use tax, sales from other states, sourcing rules (origin vs destination), marketplace facilitator rules, sales tax holidays, special rates (e.g. utilities, motor vehicles, lodging), certificate expiry rules.

## Official sources

- Michigan Treasury, sales and use tax: https://www.michigan.gov/taxes/business-taxes/sales-use-tax
- Indiana Department of Revenue, sales tax: https://www.in.gov/dor/business-tax/sales-tax/
