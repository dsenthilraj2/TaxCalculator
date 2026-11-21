# 🇳🇿 New Zealand — GST

**Level 1 (single rate)** · Last verified: *pending, verify before use* · [Back to index](README.md)

## Summary card

| Item | Value |
|---|---|
| Tax name | Goods and Services Tax (GST) |
| Authority | Inland Revenue (IRD) |
| Standard rate | **15%** |
| Other rates | Zero-rated (0%) for exports. Some services are exempt. |
| Currency | NZD, 2 decimals |
| Usual price display | **Tax-inclusive** for consumers |
| Registration threshold | NZ$60,000 annual turnover |
| Levels of government | One (national) |

## What is taxed at which rate

| Category | Treatment | Examples |
|---|---|---|
| Almost all goods and services | **15%** | **Including food**, medicines, clothing, books, energy |
| Exports | **Zero-rated (0%)** | Goods shipped to a customer outside New Zealand |
| Financial services | **Exempt** | Loan interest, bank fees |
| Residential rent | **Exempt** | Renting a home |

New Zealand is one of the simplest GST systems: there's **no food exemption**, so groceries are 15% too.

## How to calculate

- **Price excludes GST:** `GST = price × 15%`
- **Price includes GST:** `GST = price × 3 ÷ 23`
- Round per line to the cent, half-up (simplified).
- A business customer is still charged GST.

## Worked examples

| # | Situation | Calculation | GST | Total |
|---|---|---|---|---|
| 1 | Desk NZ$200.00 (ex GST) | 200.00 × 15% | **NZ$30.00** | NZ$230.00 |
| 2 | Same desk, price NZ$230.00 incl GST | 230.00 × 3 ÷ 23 | **NZ$30.00** | NZ$230.00 |
| 3 | Groceries NZ$40.00 (ex GST) | 40.00 × 15% | **NZ$6.00** | NZ$46.00 |
| 4 | Loan fee NZ$100.00 | Exempt | **NZ$0.00** | NZ$100.00 |

## Out of scope for v1

Low-value imported goods (overseas sellers), remote services from overseas, land transactions (compulsory zero-rating), second-hand goods credits, going-concern sales.

## Official sources

- Inland Revenue, GST: https://www.ird.govt.nz/gst
