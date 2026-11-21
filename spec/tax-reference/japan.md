# 🇯🇵 Japan — Consumption Tax

**Level 2 (two rates)** · Last verified: *pending, verify before use* · [Back to index](README.md)

## Summary card

| Item | Value |
|---|---|
| Tax name | Consumption tax (消費税) |
| Authority | National Tax Agency (NTA) |
| Standard rate | **10%** (7.8% national + 2.2% local, collected together as one rate) |
| Reduced rate | **8%** (6.24% national + 1.76% local) |
| Currency | JPY, **no decimals** |
| Usual price display | **Tax-inclusive** for consumers (required) |
| Registration threshold | ¥10 million taxable sales in the base period |
| Invoice rule | Qualified invoices show the tax **per rate**, rounded **once per rate per invoice** |

## What is taxed at which rate

| Category | Treatment | Examples |
|---|---|---|
| Most goods and services | **10%** | Electronics, clothing, alcohol, books, energy |
| Food and non-alcoholic drinks (takeaway/home) | **8%** | Groceries, bottled water, takeaway bento |
| Newspaper subscriptions (published 2+ times a week) | **8%** | Daily newspaper delivered at home |
| Dining in, catering | **10%** | Restaurant meals eaten on site |
| Exports | **Exempt from tax (0%)** | Goods shipped overseas |
| Exempt | **No tax** | Insured medical care, school tuition, financial services, residential rent, land |

### The famous exception

The **same meal** is **8% as takeaway** but **10% when eaten in the restaurant**. For testing: `TSG-FOOD` = 8% and `TSG-FOOD-PREP` = 10% (dine-in).

## How to calculate

1. Group the invoice lines **by rate** (10% group and 8% group).
2. For each group: `tax = group total × rate`, then **round down to the whole yen** once per group. (Businesses may choose round down, up or half. Round down is the common choice and our test choice.)
3. Invoice tax = 10% tax + 8% tax.
- Inclusive prices: `tax = group total × rate ÷ (1 + rate)`, rounded down per group.

## Worked examples

| # | Situation | Calculation | Tax | Total |
|---|---|---|---|---|
| 1 | Headphones ¥1,000 (ex tax) | 1,000 × 10% | **¥100** | ¥1,100 |
| 2 | Groceries ¥1,000 (ex tax) | 1,000 × 8% | **¥80** | ¥1,080 |
| 3 | Headphones ¥1,000 + groceries ¥1,000 | ¥100 (10% group) + ¥80 (8% group) | **¥180** | ¥2,180 |
| 4 | Groceries ¥1,234 (ex tax) | 1,234 × 8% = 98.72 → round down | **¥98** | ¥1,332 |

## Out of scope for v1

Simplified tax system for small businesses, transitional input-credit rules, cross-border digital services (platform taxation), export exemption paperwork, duty-free shop rules.

## Official sources

- National Tax Agency, consumption tax: https://www.nta.go.jp/english/taxes/consumption_tax/
