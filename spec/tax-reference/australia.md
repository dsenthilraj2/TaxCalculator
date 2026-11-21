# 🇦🇺 Australia — GST

**Level 1 (single rate)** · Last verified: *pending, verify before use* · [Back to index](README.md)

## Summary card

| Item | Value |
|---|---|
| Tax name | Goods and Services Tax (GST) |
| Authority | Australian Taxation Office (ATO) |
| Standard rate | **10%** |
| Other rates | None. Some sales are GST-free (0%) or input-taxed (no GST). |
| Currency | AUD, 2 decimals |
| Usual price display | **Tax-inclusive** for consumers (shelf price includes GST) |
| Registration threshold | A$75,000 annual turnover (A$150,000 for non-profits) |
| Levels of government | One (national) |

## What is taxed at which rate

| Category | Treatment | Examples |
|---|---|---|
| Most goods and services | **10%** | Electronics, furniture, clothing, prepared meals, alcohol, books |
| Basic food | **GST-free (0%)** | Bread, milk, fresh fruit and vegetables, meat |
| Health / medical | **GST-free (0%)** | Prescription medicines, many medical services |
| Education | **GST-free (0%)** | Recognised courses and tuition |
| Exports | **GST-free (0%)** | Goods shipped to a customer outside Australia |
| Financial services, residential rent | **Input-taxed (no GST)** | Loan interest, bank fees, renting a home |

## Exceptions worth knowing (food)

"Basic food" is GST-free, but these food items are **taxable at 10%**:
- hot food, restaurant and takeaway meals,
- confectionery, chips and snack foods, ice cream,
- soft drinks,
- alcohol.

For testing: `TSG-FOOD` = GST-free, `TSG-FOOD-PREP` and `TSG-ALC` = 10%.

## How to calculate

- **Price excludes GST:** `GST = price × 10%`
- **Price includes GST:** `GST = price ÷ 11`
- Round per line to the cent, half-up (simplified, see the [rules](README.md#rules-every-simple-calculator-follows-version-1)).
- A business customer is still charged GST.

## Worked examples

| # | Situation | Calculation | GST | Total |
|---|---|---|---|---|
| 1 | Office chair A$100.00 (ex GST) | 100.00 × 10% | **A$10.00** | A$110.00 |
| 2 | Same chair, price A$110.00 incl GST | 110.00 ÷ 11 | **A$10.00** | A$110.00 |
| 3 | Chair A$50.00 + bread A$20.00 (ex GST) | 5.00 + 0.00 | **A$5.00** | A$75.00 |
| 4 | Chair A$200.00 shipped to a customer in New Zealand | Export → GST-free | **A$0.00** | A$200.00 |

## Out of scope for v1

Low-value imported goods (overseas sellers), digital services sold to Australians from overseas, margin scheme for property, wine equalisation tax, luxury car tax, GST groups/branches, cash vs accrual reporting.

## Official sources

- ATO, GST: https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst
- ATO, GST-free food: https://www.ato.gov.au (search "GST and food")
