import { describe, expect, it } from 'vitest'
import { formatRate, parseProductCsv } from './format'

describe('parseProductCsv', () => {
  it('reads rows with optional columns', () => {
    const { rows, errors } = parseProductCsv(
      'sku,name,group,tax_category\nA,Apple,Groceries,\nB,"Book, hardcover",,TSG-BOOK',
    )
    expect(errors).toEqual([])
    expect(rows).toEqual([
      { sku: 'A', name: 'Apple', group: 'Groceries', tax_category: undefined },
      { sku: 'B', name: 'Book, hardcover', group: undefined, tax_category: 'TSG-BOOK' },
    ])
  })

  it('requires sku and name columns and values', () => {
    expect(parseProductCsv('name\nX').errors[0]).toMatch(/sku/)
    expect(parseProductCsv('sku,name\n,Missing sku').errors).toEqual([
      'Row 2: sku and name are required.',
    ])
  })

  it('handles escaped quotes', () => {
    expect(parseProductCsv('sku,name\nQ,"The ""best"" kettle"').rows[0]?.name).toBe(
      'The "best" kettle',
    )
  })
})

describe('formatRate', () => {
  it('formats decimal strings as percentages', () => {
    expect(formatRate('0.1')).toBe('10%')
    expect(formatRate('0.08')).toBe('8%')
    expect(formatRate('0.0625')).toBe('6.25%')
  })
})
