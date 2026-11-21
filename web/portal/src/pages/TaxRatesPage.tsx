import { useMemo } from 'react'
import {
  Card,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material'
import { useJurisdictions, useTaxCategories } from '../api/hooks'
import { ErrorAlert, PageHeader } from '../components/common'
import { formatRate, treatmentLabel } from '../format'

const ZERO_COLOURS: Record<string, 'default' | 'success' | 'info' | 'warning'> = {
  zero_rated: 'success',
  gst_free: 'success',
  exempt: 'info',
  input_taxed: 'info',
  not_taxable: 'default',
}

export function TaxRatesPage() {
  const jurisdictions = useJurisdictions()
  const categories = useTaxCategories()
  const table = useMemo(
    () =>
      new Map(
        (jurisdictions.data ?? []).map((j) => [
          j.code,
          new Map(j.categories.map((c) => [c.tax_category, c])),
        ]),
      ),
    [jurisdictions.data],
  )

  return (
    <>
      <PageHeader
        title="Countries & rates"
        subtitle="How the TSG sample calculator treats each product category (spec/tax-reference). Simplified for testing and demos, not for compliance."
      />
      <ErrorAlert error={jurisdictions.error ?? categories.error} />
      <Card>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Category</TableCell>
                {jurisdictions.data?.map((j) => (
                  <TableCell key={j.code} align="center">
                    <Tooltip title={`${j.name} · ${j.tax_name} · ${j.currency}`}>
                      <span>{j.code}</span>
                    </Tooltip>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {categories.data?.map((category) => (
                <TableRow key={category.code} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {category.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {category.code}
                    </Typography>
                  </TableCell>
                  {jurisdictions.data?.map((j) => {
                    const rate = table.get(j.code)?.get(category.code)
                    if (!rate) {
                      return (
                        <TableCell key={j.code} align="center">
                          <Tooltip title="Not in the simple engine yet (verify with the official source)">
                            <Typography variant="caption" color="text.disabled">
                              verify
                            </Typography>
                          </Tooltip>
                        </TableCell>
                      )
                    }
                    const zeroColour = ZERO_COLOURS[rate.treatment]
                    return (
                      <TableCell key={j.code} align="center">
                        {zeroColour ? (
                          <Chip size="small" color={zeroColour} label={treatmentLabel(rate.treatment)} />
                        ) : (
                          <Chip
                            size="small"
                            variant={rate.treatment === 'reduced' ? 'filled' : 'outlined'}
                            color={rate.treatment === 'reduced' ? 'secondary' : 'default'}
                            label={formatRate(rate.rate)}
                          />
                        )}
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </>
  )
}
