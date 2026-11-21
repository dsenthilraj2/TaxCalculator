# 🇬🇧 United Kingdom — VAT

**Level 2 (three rates)** · Last verified: *pending, verify before use* · [Back to index](README.md)

## Summary card

| Item | Value |
|---|---|
| Tax name | Value Added Tax (VAT) |
| Authority | HM Revenue & Customs (HMRC) |
| Standard rate | **20%** |
| Reduced rate | **5%** |
| Zero rate | **0%** |
| Currency | GBP, 2 decimals |
| Usual price display | **Tax-inclusive** for consumers |
| Registration threshold | £90,000 taxable turnover (since April 2024) |
| Levels of government | One (national) |

## What is taxed at which rate

| Category | Rate | Examples |
|---|---|---|
| Most goods and services | **20%** | Electronics, adult clothing, alcohol, restaurant and hot takeaway food |
| Home energy | **5%** | Household electricity and gas |
| Children's car seats | **5%** | |
| Most food | **0%** | Bread, milk, fruit, vegetables |
| Children's clothing and shoes | **0%** | |
| Books, newspapers | **0%** | Printed books and newspapers |
| Prescription medicines (dispensed) | **0%** | |
| Exports of goods | **0%** | Goods shipped outside the UK |
| Exempt | **No VAT** | Insurance, finance, education by eligible bodies, health services, some postal services |

### Exceptions worth knowing (food)

Food is mostly 0%, but these are **20%**: hot takeaway food, restaurant meals, confectionery, crisps, ice cream, soft drinks, alcohol.

### Zero-rated vs exempt

Both mean £0 VAT on the invoice. The difference matters for the seller's reporting and reclaiming, so our calculator labels them differently (`ZERO_RATED` vs `EXEMPT`).

## How to calculate

- **Price excludes VAT:** `VAT = price × rate`
- **Price includes VAT:** `VAT = price × rate ÷ (1 + rate)`. At 20% that's price ÷ 6.
- Round per line to the penny, half-up (simplified; HMRC allows other methods).
- A business customer is still charged VAT.

## Worked examples

| # | Situation | Calculation | VAT | Total |
|---|---|---|---|---|
| 1 | Kettle £100.00 (ex VAT) | 100.00 × 20% | **£20.00** | £120.00 |
| 2 | Home electricity £100.00 | 100.00 × 5% | **£5.00** | £105.00 |
| 3 | Children's coat £100.00 | Zero-rated | **£0.00** | £100.00 |
| 4 | Kettle £100 + children's coat £40 + electricity £60 | 20.00 + 0.00 + 3.00 | **£23.00** | £223.00 |
| 5 | Kettle priced £120.00 incl VAT | 120.00 ÷ 6 | **£20.00** | £120.00 |

## Out of scope for v1

Northern Ireland (EU goods rules), imports and the £135 low-value rule, reverse charge (construction, services from abroad), Flat Rate Scheme, margin schemes, partial exemption, VAT on energy-saving materials changes.

## Official sources

- HMRC, VAT rates on goods and services: https://www.gov.uk/guidance/rates-of-vat-on-different-goods-and-services
- VAT registration: https://www.gov.uk/vat-registration
