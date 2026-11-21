import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  ListSubheader,
  MenuItem,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteOutline from '@mui/icons-material/DeleteOutlined'
import CalculateOutlined from '@mui/icons-material/CalculateOutlined'
import CheckCircle from '@mui/icons-material/CheckCircle'
import Cancel from '@mui/icons-material/Cancel'
import RestartAlt from '@mui/icons-material/RestartAlt'
import {
  useCalculate,
  useJurisdictions,
  useProducts,
  useScenarios,
  useTaxCategories,
} from '../api/hooks'
import {
  ApiError,
  type CalculateRequest,
  type CalculateResponse,
  type JurisdictionInfo,
  type Scenario,
} from '../api/client'
import { CategoryChip, ErrorAlert, PageHeader } from '../components/common'
import { formatMoney, formatRate, treatmentLabel } from '../format'

interface LineForm {
  key: number
  sku: string
  tax_category: string
  quantity: string
  unit_price: string
}

interface AddressForm {
  country: string
  region: string
  city: string
}

interface FormState {
  reference: string
  currency: string
  prices_include_tax: boolean
  ship_from: AddressForm
  ship_to: AddressForm
  exemption: 'none' | 'resale'
  lines: LineForm[]
}

let nextKey = 1
const newLine = (partial: Partial<LineForm> = {}): LineForm => ({
  key: nextKey++,
  sku: '',
  tax_category: '',
  quantity: '1',
  unit_price: '',
  ...partial,
})

const EMPTY_FORM: FormState = {
  reference: '',
  currency: 'AUD',
  prices_include_tax: false,
  ship_from: { country: 'AU', region: 'NSW', city: 'Sydney' },
  ship_to: { country: 'AU', region: '', city: 'Melbourne' },
  exemption: 'none',
  lines: [newLine({ sku: 'LAMP-DESK', unit_price: '50.00' })],
}

const EXTRA_COUNTRIES = ['CA', 'FR', 'DE']

function formFromScenario(scenario: Scenario): FormState {
  const request = scenario.request
  const address = (a?: { country: string; region?: string | null; city?: string | null }) => ({
    country: a?.country ?? '',
    region: a?.region ?? '',
    city: a?.city ?? '',
  })
  return {
    reference: request.reference ?? scenario.id,
    currency: request.currency,
    prices_include_tax: request.prices_include_tax ?? false,
    ship_from: address(request.ship_from),
    ship_to: address(request.ship_to),
    exemption: request.customer?.exemption === 'resale' ? 'resale' : 'none',
    lines: request.lines.map((line) =>
      newLine({
        sku: line.sku ?? '',
        tax_category: line.tax_category ?? '',
        quantity: String(line.quantity ?? '1'),
        unit_price: String(line.unit_price),
      }),
    ),
  }
}

function requestFromForm(form: FormState, includeShipTo: boolean): CalculateRequest {
  const address = (a: AddressForm) => ({
    country: a.country,
    region: a.region || null,
    city: a.city || null,
  })
  const request: CalculateRequest = {
    reference: form.reference || null,
    currency: form.currency,
    prices_include_tax: form.prices_include_tax,
    ship_from: address(form.ship_from),
    ship_to: address(form.ship_to),
    customer: { exemption: form.exemption },
    lines: form.lines.map((line) => ({
      sku: line.sku || null,
      tax_category: line.tax_category || null,
      quantity: line.quantity,
      unit_price: line.unit_price,
    })),
  }
  if (!includeShipTo) delete (request as Partial<CalculateRequest>).ship_to
  return request
}

export function CalculatorPage() {
  const [params, setParams] = useSearchParams()
  const scenarios = useScenarios().data
  const jurisdictions = useJurisdictions().data ?? []
  const categoryData = useTaxCategories().data
  const categories = useMemo(() => categoryData ?? [], [categoryData])
  const names = useMemo(() => new Map(categories.map((c) => [c.code, c.name])), [categories])
  const calculate = useCalculate()
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [scenario, setScenario] = useState<Scenario | null>(null)

  // Load ?scenario=ID (e.g. from a dashboard quick link) once, when scenarios first arrive.
  // Later changes come from the picker, which keeps the URL in sync only for sharing.
  // Adjusting state during render is React's recommended alternative to an effect here.
  const [urlHandled, setUrlHandled] = useState(false)
  if (!urlHandled && scenarios) {
    setUrlHandled(true)
    const found = scenarios.find((s) => s.id === params.get('scenario'))
    if (found) {
      setScenario(found)
      setForm(formFromScenario(found))
    }
  }

  const loadScenario = (next: Scenario | null) => {
    setScenario(next)
    calculate.reset()
    if (next) {
      setForm(formFromScenario(next))
      setParams({ scenario: next.id }, { replace: true })
    } else {
      setParams({}, { replace: true })
    }
  }

  const reset = () => {
    loadScenario(null)
    setForm({ ...EMPTY_FORM, lines: [newLine({ sku: 'LAMP-DESK', unit_price: '50.00' })] })
  }

  const update = (patch: Partial<FormState>) => setForm((current) => ({ ...current, ...patch }))
  const updateLine = (key: number, patch: Partial<LineForm>) =>
    setForm((current) => ({
      ...current,
      lines: current.lines.map((line) => (line.key === key ? { ...line, ...patch } : line)),
    }))

  const onSellerChange = (address: AddressForm) => {
    const match = findJurisdiction(jurisdictions, address)
    update({ ship_from: address, ...(match ? { currency: match.currency } : {}) })
  }

  // A scenario may deliberately omit the ship-to address (NEG-05).
  const omitShipTo = scenario !== null && !scenario.request.ship_to && !form.ship_to.country
  const submit = () => calculate.mutate(requestFromForm(form, !omitShipTo))

  const destination = findJurisdiction(jurisdictions, form.ship_to)
  const showExemption = destination?.customer_exemptions ?? form.ship_to.country === 'US'

  return (
    <>
      <PageHeader
        title="Sample calculator"
        subtitle="Calculate tax with the TSG sample engine for the documented countries. Lines can use your product SKUs or an explicit tax category."
        actions={
          <Button startIcon={<RestartAlt />} onClick={reset}>
            Reset
          </Button>
        }
      />

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent>
              <Autocomplete
                options={scenarios ?? []}
                groupBy={(option) => option.group}
                getOptionLabel={(option) => `${option.id} — ${option.title}`}
                value={scenario}
                onChange={(_, value) => loadScenario(value)}
                isOptionEqualToValue={(a, b) => a.id === b.id}
                renderInput={(inputProps) => (
                  <TextField
                    {...inputProps}
                    label="Load a test scenario (optional)"
                    helperText="From spec/tax-reference/test-scenarios.md, with the expected answer"
                  />
                )}
                sx={{ mb: 3 }}
              />

              <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <AddressFields
                    title="Seller (ship from)"
                    value={form.ship_from}
                    onChange={onSellerChange}
                    jurisdictions={jurisdictions}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <AddressFields
                    title="Customer (ship to)"
                    value={form.ship_to}
                    onChange={(ship_to) => update({ ship_to })}
                    jurisdictions={jurisdictions}
                  />
                </Grid>
              </Grid>

              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                sx={{ mt: 2, alignItems: { sm: 'center' } }}
              >
                <TextField
                  label="Currency"
                  size="small"
                  value={form.currency}
                  onChange={(e) => update({ currency: e.target.value.toUpperCase() })}
                  sx={{ width: 120 }}
                />
                <TextField
                  label="Reference"
                  size="small"
                  value={form.reference}
                  onChange={(e) => update({ reference: e.target.value })}
                  placeholder="e.g. SO-1001"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={form.prices_include_tax}
                      onChange={(e) => update({ prices_include_tax: e.target.checked })}
                    />
                  }
                  label="Prices include tax"
                />
                {showExemption && (
                  <TextField
                    select
                    size="small"
                    label="Customer exemption"
                    value={form.exemption}
                    onChange={(e) => update({ exemption: e.target.value as 'none' | 'resale' })}
                    sx={{ minWidth: 180 }}
                  >
                    <MenuItem value="none">None</MenuItem>
                    <MenuItem value="resale">Resale certificate</MenuItem>
                  </TextField>
                )}
              </Stack>

              <Divider sx={{ my: 3 }} />
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                Lines
              </Typography>
              <Stack spacing={1.5}>
                {form.lines.map((line, index) => (
                  <LineFields
                    key={line.key}
                    index={index}
                    line={line}
                    categories={categories}
                    onChange={(patch) => updateLine(line.key, patch)}
                    onRemove={
                      form.lines.length > 1
                        ? () => update({ lines: form.lines.filter((l) => l.key !== line.key) })
                        : undefined
                    }
                  />
                ))}
              </Stack>
              <Stack direction="row" spacing={1.5} sx={{ mt: 2 }}>
                <Button
                  startIcon={<AddIcon />}
                  onClick={() => update({ lines: [...form.lines, newLine()] })}
                >
                  Add line
                </Button>
                <Box sx={{ flexGrow: 1 }} />
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<CalculateOutlined />}
                  onClick={submit}
                  disabled={calculate.isPending}
                >
                  Calculate tax
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 5 }}>
          <Stack spacing={2.5}>
            {scenario && (
              <ExpectedCard scenario={scenario} result={calculate.data} error={calculate.error} />
            )}
            <ErrorAlert error={calculate.error} />
            {calculate.data ? (
              <ResultCard result={calculate.data} names={names} />
            ) : (
              !calculate.error && (
                <Card>
                  <CardContent sx={{ py: 6, textAlign: 'center' }}>
                    <CalculateOutlined sx={{ fontSize: 48, color: 'text.disabled' }} />
                    <Typography color="text.secondary" sx={{ mt: 1 }}>
                      Fill in the sale and press <strong>Calculate tax</strong>.
                    </Typography>
                  </CardContent>
                </Card>
              )
            )}
          </Stack>
        </Grid>
      </Grid>
    </>
  )
}

function findJurisdiction(
  jurisdictions: JurisdictionInfo[],
  address: AddressForm,
): JurisdictionInfo | undefined {
  if (address.country === 'US') {
    return jurisdictions.find((j) => j.country === 'US' && j.region === address.region)
  }
  return jurisdictions.find((j) => j.country === address.country && !j.region)
}

function AddressFields({
  title,
  value,
  onChange,
  jurisdictions,
}: {
  title: string
  value: AddressForm
  onChange: (value: AddressForm) => void
  jurisdictions: JurisdictionInfo[]
}) {
  const countries = [...new Set(jurisdictions.map((j) => j.country))]
  const usStates = jurisdictions.filter((j) => j.country === 'US').map((j) => j.region ?? '')
  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2" color="text.secondary">
        {title}
      </Typography>
      <Stack direction="row" spacing={1.5}>
        <TextField
          select
          size="small"
          label="Country"
          value={value.country}
          onChange={(e) => onChange({ ...value, country: e.target.value, region: '' })}
          sx={{ flex: 1 }}
        >
          <MenuItem value="">
            <em>None</em>
          </MenuItem>
          <ListSubheader>Supported</ListSubheader>
          {countries.map((country) => (
            <MenuItem key={country} value={country}>
              {jurisdictions.find((j) => j.country === country && !j.region)?.name ??
                'United States'}{' '}
              ({country})
            </MenuItem>
          ))}
          <ListSubheader>Not supported (for testing)</ListSubheader>
          {EXTRA_COUNTRIES.map((country) => (
            <MenuItem key={country} value={country}>
              {country}
            </MenuItem>
          ))}
        </TextField>
        <Autocomplete
          freeSolo
          options={value.country === 'US' ? [...usStates, 'CO', 'CA', 'NY'] : []}
          inputValue={value.region}
          onInputChange={(_, region) => onChange({ ...value, region: region.toUpperCase() })}
          sx={{ width: 130 }}
          renderInput={(inputProps) => (
            <TextField {...inputProps} size="small" label="State/region" />
          )}
        />
      </Stack>
      <TextField
        size="small"
        label="City"
        value={value.city}
        onChange={(e) => onChange({ ...value, city: e.target.value })}
      />
    </Stack>
  )
}

function LineFields({
  index,
  line,
  categories,
  onChange,
  onRemove,
}: {
  index: number
  line: LineForm
  categories: { code: string; name: string }[]
  onChange: (patch: Partial<LineForm>) => void
  onRemove?: () => void
}) {
  const products = useProducts({ status: 'all' }).data ?? []
  const product = products.find((p) => p.sku === line.sku)
  return (
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ alignItems: 'flex-start' }}>
      <Chip label={index + 1} size="small" sx={{ mt: 1 }} />
      <Autocomplete
        freeSolo
        options={products.map((p) => p.sku)}
        inputValue={line.sku}
        onInputChange={(_, sku) => onChange({ sku })}
        sx={{ flex: 2, minWidth: 160 }}
        renderOption={(props, sku) => {
          const p = products.find((x) => x.sku === sku)
          return (
            <li {...props} key={sku}>
              <Box>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {sku}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {p?.name} · {p?.resolved_category}
                </Typography>
              </Box>
            </li>
          )
        }}
        renderInput={(inputProps) => (
          <TextField
            {...inputProps}
            size="small"
            label="SKU"
            helperText={
              product
                ? `${product.name} → ${product.resolved_category}`
                : line.sku
                  ? 'Unknown SKU: default category'
                  : ' '
            }
          />
        )}
      />
      <TextField
        select
        size="small"
        label="Category override"
        value={line.tax_category}
        onChange={(e) => onChange({ tax_category: e.target.value })}
        sx={{ flex: 2, minWidth: 160 }}
        helperText=" "
      >
        <MenuItem value="">
          <em>From product setup</em>
        </MenuItem>
        {categories.map((c) => (
          <MenuItem key={c.code} value={c.code}>
            {c.code}
          </MenuItem>
        ))}
        <MenuItem value="TSG-UNKNOWN">TSG-UNKNOWN (invalid, for testing)</MenuItem>
      </TextField>
      <TextField
        size="small"
        label="Qty"
        value={line.quantity}
        onChange={(e) => onChange({ quantity: e.target.value })}
        sx={{ width: 80 }}
        helperText=" "
      />
      <TextField
        size="small"
        label="Unit price"
        value={line.unit_price}
        onChange={(e) => onChange({ unit_price: e.target.value })}
        sx={{ width: 120 }}
        helperText=" "
      />
      <Tooltip title="Remove line">
        <span>
          <IconButton onClick={onRemove} disabled={!onRemove} sx={{ mt: 0.5 }}>
            <DeleteOutline />
          </IconButton>
        </span>
      </Tooltip>
    </Stack>
  )
}

function ExpectedCard({
  scenario,
  result,
  error,
}: {
  scenario: Scenario
  result?: CalculateResponse
  error: unknown
}) {
  const expected = scenario.expected
  let verdict: boolean | null = null
  if (expected.status === 200 && result) {
    verdict = result.tax_total === expected.tax_total && result.gross_total === expected.gross_total
  } else if (expected.status === 422 && error instanceof ApiError) {
    verdict = error.status === 422 && error.problemType === expected.problem_type
  } else if (result || error) {
    verdict = false
  }
  return (
    <Alert
      severity={verdict === null ? 'info' : verdict ? 'success' : 'error'}
      icon={verdict === null ? undefined : verdict ? <CheckCircle /> : <Cancel />}
    >
      <Typography variant="subtitle2">
        {scenario.id} — {scenario.title}
      </Typography>
      {expected.status === 200 ? (
        <Typography variant="body2">
          Expected tax <strong>{expected.tax_total}</strong>, total{' '}
          <strong>{expected.gross_total}</strong>
          {result && ` · got ${result.tax_total} / ${result.gross_total}`}
        </Typography>
      ) : (
        <Typography variant="body2">
          Expected to be rejected: <code>{expected.problem_type}</code>
          {error instanceof ApiError && ` · got ${error.problemType}`}
        </Typography>
      )}
      {verdict !== null && (
        <Typography variant="body2" sx={{ fontWeight: 600, mt: 0.5 }}>
          {verdict ? 'Matches the documented answer.' : 'Does not match the documented answer.'}
        </Typography>
      )}
    </Alert>
  )
}

function ResultCard({ result, names }: { result: CalculateResponse; names: Map<string, string> }) {
  const money = (value: string) => formatMoney(value, result.currency)
  return (
    <Card>
      <CardHeader
        title={`${result.tax_name}: ${money(result.tax_total)}`}
        subheader={`${result.jurisdiction_name} · responded by ${result.responded_by} · rules ${result.rules_version}`}
      />
      <CardContent sx={{ pt: 0 }}>
        <Stack direction="row" spacing={3} sx={{ mb: 2 }}>
          <Total label="Net" value={money(result.net_total)} />
          <Total label="Tax" value={money(result.tax_total)} />
          <Total label="Total" value={money(result.gross_total)} strong />
        </Stack>
        {result.prices_include_tax && (
          <Chip size="small" label="Prices included tax" sx={{ mb: 1.5 }} />
        )}
      </CardContent>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Treatment</TableCell>
              <TableCell align="right">Rate</TableCell>
              <TableCell align="right">Net</TableCell>
              <TableCell align="right">Tax</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {result.lines.map((line) => (
              <TableRow key={line.line_id}>
                <TableCell>
                  {line.line_id}
                  {line.sku && (
                    <Typography variant="caption" color="text.secondary" component="div">
                      {line.sku}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <CategoryChip
                    code={line.tax_category}
                    source={line.category_source}
                    names={names}
                  />
                </TableCell>
                <TableCell>{treatmentLabel(line.treatment)}</TableCell>
                <TableCell align="right">{formatRate(line.rate)}</TableCell>
                <TableCell align="right">{money(line.net_amount)}</TableCell>
                <TableCell align="right">{money(line.tax_amount)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  )
}

function Total({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant={strong ? 'h6' : 'body1'} sx={{ fontWeight: strong ? 700 : 500 }}>
        {value}
      </Typography>
    </Box>
  )
}
