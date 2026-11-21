import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  InputAdornment,
  MenuItem,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteOutline from '@mui/icons-material/DeleteOutlined'
import EditOutlined from '@mui/icons-material/EditOutlined'
import SearchIcon from '@mui/icons-material/Search'
import UploadFileOutlined from '@mui/icons-material/UploadFileOutlined'
import {
  useDeleteGroup,
  useDeleteProduct,
  useGroups,
  useImportProducts,
  useProducts,
  useSaveGroup,
  useSaveProduct,
  useSaveTaxSettings,
  useSetupSummary,
  useTaxCategories,
  useTaxSettings,
} from '../api/hooks'
import type { ProductView, TaxCategory } from '../api/client'
import { CategoryChip, ErrorAlert, PageHeader } from '../components/common'
import { parseProductCsv } from '../format'

type Status = 'all' | 'mapped' | 'unmapped'

function useCategoryNames(categories: TaxCategory[] | undefined) {
  return useMemo(() => new Map((categories ?? []).map((c) => [c.code, c.name])), [categories])
}

export function ProductsPage() {
  const [params, setParams] = useSearchParams()
  const tab = params.get('tab') ?? 'products'
  const summary = useSetupSummary().data
  return (
    <>
      <PageHeader
        title="Products & tax categories"
        subtitle="Map what you sell to a TSG tax category once. Every calculator uses the same mapping, so you can switch provider any time."
      />
      <Card sx={{ mb: 2.5 }}>
        <Tabs
          value={tab}
          onChange={(_, value: string) => setParams({ tab: value })}
          sx={{ px: 2, borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab value="products" label={`Products${summary ? ` (${summary.products_total})` : ''}`} />
          <Tab value="groups" label={`Product groups${summary ? ` (${summary.groups_total})` : ''}`} />
          <Tab value="settings" label="Default category" />
        </Tabs>
        <Box sx={{ p: { xs: 2, sm: 2.5 } }}>
          {tab === 'products' && <ProductsTab />}
          {tab === 'groups' && <GroupsTab />}
          {tab === 'settings' && <SettingsTab />}
        </Box>
      </Card>
      <LookupExplainer />
    </>
  )
}

// ------------------------------------------------------------------ products
function ProductsTab() {
  const [params, setParams] = useSearchParams()
  const status = (params.get('status') as Status | null) ?? 'all'
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [editing, setEditing] = useState<ProductView | 'new' | null>(null)
  const [importing, setImporting] = useState(false)
  const categories = useTaxCategories().data
  const names = useCategoryNames(categories)
  const products = useProducts({ search, category, status })
  const remove = useDeleteProduct()

  return (
    <>
      <Stack
        direction="row"
        spacing={1.5}
        useFlexGap
        sx={{ mb: 2, alignItems: 'center', flexWrap: 'wrap' }}
      >
        <TextField
          size="small"
          placeholder="Search SKU, name, group"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: 240 }}
        />
        <TextField
          select
          size="small"
          label="Category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="">All categories</MenuItem>
          {categories?.map((c) => (
            <MenuItem key={c.code} value={c.code}>
              {c.name}
            </MenuItem>
          ))}
        </TextField>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={status}
          onChange={(_, value: Status | null) => {
            if (value) setParams({ tab: 'products', status: value })
          }}
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="mapped">Mapped</ToggleButton>
          <ToggleButton value="unmapped">Using default</ToggleButton>
        </ToggleButtonGroup>
        <Box sx={{ flexGrow: 1 }} />
        <Button startIcon={<UploadFileOutlined />} onClick={() => setImporting(true)}>
          Import CSV
        </Button>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setEditing('new')}>
          Add product
        </Button>
      </Stack>

      <ErrorAlert error={products.error ?? remove.error} />
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>SKU</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Group</TableCell>
              <TableCell>Tax category</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {products.data?.map((product) => (
              <TableRow key={product.sku} hover>
                <TableCell sx={{ fontFamily: 'monospace' }}>{product.sku}</TableCell>
                <TableCell>
                  {product.name}
                  {product.description && (
                    <Typography variant="caption" color="text.secondary" component="div">
                      {product.description}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>{product.group ?? '—'}</TableCell>
                <TableCell>
                  <CategoryChip
                    code={product.resolved_category}
                    source={product.category_source}
                    names={names}
                  />
                </TableCell>
                <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={() => setEditing(product)}>
                      <EditOutlined fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton
                      size="small"
                      onClick={() => {
                        if (window.confirm(`Delete product ${product.sku}?`)) {
                          remove.mutate(product.sku)
                        }
                      }}
                    >
                      <DeleteOutline fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {products.data?.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} sx={{ py: 5, textAlign: 'center', color: 'text.secondary' }}>
                  No products match. Add one, or import a CSV.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {editing && (
        <ProductDialog
          product={editing === 'new' ? null : editing}
          categories={categories ?? []}
          onClose={() => setEditing(null)}
        />
      )}
      {importing && <ImportDialog onClose={() => setImporting(false)} />}
    </>
  )
}

function ProductDialog({
  product,
  categories,
  onClose,
}: {
  product: ProductView | null
  categories: TaxCategory[]
  onClose: () => void
}) {
  const groups = useGroups().data ?? []
  const save = useSaveProduct()
  const [sku, setSku] = useState(product?.sku ?? '')
  const [name, setName] = useState(product?.name ?? '')
  const [group, setGroup] = useState(product?.group ?? '')
  const [category, setCategory] = useState(product?.tax_category ?? '')
  const [description, setDescription] = useState(product?.description ?? '')
  const groupCategory = groups.find((g) => g.group === group)?.tax_category

  const submit = () =>
    save.mutate(
      {
        sku: sku.trim(),
        name: name.trim(),
        group: group.trim() || null,
        tax_category: category || null,
        description: description.trim() || null,
      },
      { onSuccess: onClose },
    )

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{product ? `Edit ${product.sku}` : 'Add product'}</DialogTitle>
      <DialogContent>
        <ErrorAlert error={save.error} />
        <Stack spacing={2} sx={{ mt: 1 }}>
          <TextField
            label="SKU"
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            disabled={Boolean(product)}
            required
            autoFocus={!product}
          />
          <TextField label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Autocomplete
            freeSolo
            options={groups.map((g) => g.group)}
            value={group}
            onInputChange={(_, value) => setGroup(value)}
            renderInput={(inputProps) => (
              <TextField
                {...inputProps}
                label="Product group (optional)"
                helperText={
                  groupCategory
                    ? `This group maps to ${groupCategory}`
                    : group
                      ? 'This group has no mapping yet'
                      : 'Products inherit the category of their group'
                }
              />
            )}
          />
          <TextField
            select
            label="Tax category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            helperText="Leave as 'Inherit' to use the group's category, or the default"
          >
            <MenuItem value="">
              <em>Inherit from group / default</em>
            </MenuItem>
            {categories.map((c) => (
              <MenuItem key={c.code} value={c.code}>
                {c.name} ({c.code})
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            minRows={2}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={submit}
          disabled={!sku.trim() || !name.trim() || save.isPending}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  )
}

const CSV_EXAMPLE = `sku,name,group,tax_category
BREAD-RYE,Rye bread,Groceries,
KIDS-HAT,Kids beanie,Kids clothing,
GIFT-CARD,Gift card,,TSG-FIN`

function ImportDialog({ onClose }: { onClose: () => void }) {
  const [text, setText] = useState(CSV_EXAMPLE)
  const importProducts = useImportProducts()
  const parsed = useMemo(() => parseProductCsv(text), [text])

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Import products from CSV</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Paste CSV with a header row: <code>sku,name,group,tax_category</code>. Existing SKUs are
          replaced. Leave <code>tax_category</code> empty to inherit from the group.
        </Typography>
        <ErrorAlert error={importProducts.error} />
        {importProducts.data && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Imported {importProducts.data.imported} products.
          </Alert>
        )}
        <TextField
          value={text}
          onChange={(e) => setText(e.target.value)}
          multiline
          minRows={8}
          fullWidth
          slotProps={{ htmlInput: { style: { fontFamily: 'monospace', fontSize: 13 } } }}
        />
        <Stack direction="row" spacing={2} sx={{ mt: 1.5 }}>
          <Typography variant="body2">{parsed.rows.length} rows ready</Typography>
          {parsed.errors.map((error) => (
            <Typography key={error} variant="body2" color="error">
              {error}
            </Typography>
          ))}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button
          variant="contained"
          disabled={parsed.rows.length === 0 || parsed.errors.length > 0 || importProducts.isPending}
          onClick={() =>
            importProducts.mutate(
              parsed.rows.map((row) => ({
                sku: row.sku,
                name: row.name,
                group: row.group ?? null,
                tax_category: row.tax_category ?? null,
              })),
            )
          }
        >
          Import {parsed.rows.length} products
        </Button>
      </DialogActions>
    </Dialog>
  )
}

// ------------------------------------------------------------------ groups
function GroupsTab() {
  const groups = useGroups()
  const categories = useTaxCategories().data ?? []
  const products = useProducts({ status: 'all' }).data ?? []
  const save = useSaveGroup()
  const remove = useDeleteGroup()
  const [newGroup, setNewGroup] = useState('')
  const [newCategory, setNewCategory] = useState('')

  const productGroups = new Set(products.map((p) => p.group).filter(Boolean) as string[])
  const mapped = new Set((groups.data ?? []).map((g) => g.group))
  const suggestions = [...productGroups].filter((g) => !mapped.has(g)).sort()

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Map a whole product group (as it appears in your ERP) to a category. Every product in the
        group inherits it unless the product sets its own.
      </Typography>
      <ErrorAlert error={groups.error ?? save.error ?? remove.error} />
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
        <Autocomplete
          freeSolo
          options={suggestions}
          inputValue={newGroup}
          onInputChange={(_, value) => setNewGroup(value)}
          sx={{ minWidth: 240 }}
          renderInput={(inputProps) => (
            <TextField
              {...inputProps}
              size="small"
              label="Group"
              helperText={suggestions.length ? `${suggestions.length} unmapped groups found` : ' '}
            />
          )}
        />
        <TextField
          select
          size="small"
          label="Tax category"
          value={newCategory}
          onChange={(e) => setNewCategory(e.target.value)}
          sx={{ minWidth: 240 }}
          helperText=" "
        >
          {categories.map((c) => (
            <MenuItem key={c.code} value={c.code}>
              {c.name} ({c.code})
            </MenuItem>
          ))}
        </TextField>
        <Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            disabled={!newGroup.trim() || !newCategory || save.isPending}
            onClick={() =>
              save.mutate(
                { group: newGroup.trim(), tax_category: newCategory },
                {
                  onSuccess: () => {
                    setNewGroup('')
                    setNewCategory('')
                  },
                },
              )
            }
          >
            Map group
          </Button>
        </Box>
      </Stack>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Group</TableCell>
              <TableCell>Tax category</TableCell>
              <TableCell align="right">Products</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.data?.map((mapping) => (
              <TableRow key={mapping.group} hover>
                <TableCell>{mapping.group}</TableCell>
                <TableCell sx={{ minWidth: 240 }}>
                  <TextField
                    select
                    size="small"
                    variant="standard"
                    value={mapping.tax_category}
                    onChange={(e) =>
                      save.mutate({ group: mapping.group, tax_category: e.target.value })
                    }
                    fullWidth
                  >
                    {categories.map((c) => (
                      <MenuItem key={c.code} value={c.code}>
                        {c.name} ({c.code})
                      </MenuItem>
                    ))}
                  </TextField>
                </TableCell>
                <TableCell align="right">
                  {products.filter((p) => p.group === mapping.group).length}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Remove mapping">
                    <IconButton size="small" onClick={() => remove.mutate(mapping.group)}>
                      <DeleteOutline fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {groups.data?.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} sx={{ py: 5, textAlign: 'center', color: 'text.secondary' }}>
                  No group mappings yet.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  )
}

// ------------------------------------------------------------------ settings
function SettingsTab() {
  const settings = useTaxSettings()
  const categories = useTaxCategories().data ?? []
  const save = useSaveTaxSettings()
  return (
    <Box sx={{ maxWidth: 520 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Used for any product that has no category of its own and no group mapping, so you can start
        calculating on day one and tidy up later.
      </Typography>
      <ErrorAlert error={settings.error ?? save.error} />
      {settings.data && (
        <TextField
          select
          fullWidth
          label="Default tax category"
          value={settings.data.default_category}
          onChange={(e) => save.mutate(e.target.value)}
          helperText={save.isSuccess ? 'Saved.' : ' '}
        >
          {categories.map((c) => (
            <MenuItem key={c.code} value={c.code}>
              {c.name} ({c.code}) — {c.description}
            </MenuItem>
          ))}
        </TextField>
      )}
    </Box>
  )
}

function LookupExplainer() {
  const steps = [
    ['1', 'Category on the sale line', 'Sent by the ERP for a one-off override'],
    ['2', 'Category on the product', 'Set here for a specific SKU'],
    ['3', 'Category of the product group', 'Set once for a whole group'],
    ['4', 'Default category', 'Everything else'],
  ]
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>
          How a sale line gets its tax category
        </Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          {steps.map(([number, title, text]) => (
            <Stack key={number} direction="row" spacing={1.5} sx={{ flex: 1 }}>
              <Box
                sx={{
                  width: 28,
                  height: 28,
                  borderRadius: '50%',
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  display: 'grid',
                  placeItems: 'center',
                  fontWeight: 700,
                  flexShrink: 0,
                }}
              >
                {number}
              </Box>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {text}
                </Typography>
              </Box>
            </Stack>
          ))}
        </Stack>
      </CardContent>
    </Card>
  )
}
