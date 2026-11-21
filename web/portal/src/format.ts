/** Display helpers. Amounts arrive as decimal strings and are only converted for display. */

export function formatMoney(amount: string | number, currency: string): string {
  const value = typeof amount === 'string' ? Number(amount) : amount
  const decimals = currency === 'JPY' ? 0 : 2
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value)
  } catch {
    return `${value.toFixed(decimals)} ${currency}`
  }
}

/** "0.1" -> "10%", "0.08" -> "8%". */
export function formatRate(rate: string | number): string {
  const value = (typeof rate === 'string' ? Number(rate) : rate) * 100
  return `${Number(value.toFixed(2))}%`
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(iso),
  )
}

export function currentMonthLabel(month: string): string {
  const [year, monthNumber] = month.split('-').map(Number)
  return new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(
    new Date(year ?? 2000, (monthNumber ?? 1) - 1, 1),
  )
}

export function titleCase(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

const TREATMENT_LABELS: Record<string, string> = {
  standard: 'Standard',
  reduced: 'Reduced',
  zero_rated: 'Zero-rated',
  gst_free: 'GST-free',
  exempt: 'Exempt',
  input_taxed: 'Input-taxed',
  not_taxable: 'Not taxable',
  export: 'Export (0%)',
  exempt_customer: 'Exempt customer',
}

/** Human label for a tax treatment code, e.g. "gst_free" -> "GST-free". */
export function treatmentLabel(treatment: string): string {
  return TREATMENT_LABELS[treatment] ?? titleCase(treatment)
}

/** "1 group", "2 groups". */
export function plural(count: number, singular: string, pluralForm = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : pluralForm}`
}

export interface CsvProduct {
  sku: string
  name: string
  group?: string
  tax_category?: string
}

/**
 * Parse simple CSV with a header row: sku,name,group,tax_category.
 * Supports double-quoted fields with commas. Returns rows and per-line errors.
 */
export function parseProductCsv(text: string): { rows: CsvProduct[]; errors: string[] } {
  const lines = text.split(/\r?\n/).filter((line) => line.trim() !== '')
  if (lines.length === 0) return { rows: [], errors: ['The file is empty.'] }
  const header = splitCsvLine(lines[0] ?? '').map((h) => h.trim().toLowerCase())
  const index = (name: string) => header.indexOf(name)
  if (index('sku') < 0 || index('name') < 0) {
    return { rows: [], errors: ['The header must include "sku" and "name".'] }
  }
  const rows: CsvProduct[] = []
  const errors: string[] = []
  lines.slice(1).forEach((line, i) => {
    const cells = splitCsvLine(line)
    const cell = (name: string) => (index(name) >= 0 ? (cells[index(name)] ?? '').trim() : '')
    const sku = cell('sku')
    const name = cell('name')
    if (!sku || !name) {
      errors.push(`Row ${i + 2}: sku and name are required.`)
      return
    }
    rows.push({
      sku,
      name,
      group: cell('group') || undefined,
      tax_category: cell('tax_category') || undefined,
    })
  })
  return { rows, errors }
}

function splitCsvLine(line: string): string[] {
  const cells: string[] = []
  let current = ''
  let quoted = false
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (quoted) {
      if (char === '"' && line[i + 1] === '"') {
        current += '"'
        i++
      } else if (char === '"') {
        quoted = false
      } else {
        current += char
      }
    } else if (char === '"') {
      quoted = true
    } else if (char === ',') {
      cells.push(current)
      current = ''
    } else {
      current += char
    }
  }
  cells.push(current)
  return cells
}
