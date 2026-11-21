import type { ReactNode } from 'react'
import { Alert, Box, Card, CardContent, Chip, Stack, Tooltip, Typography } from '@mui/material'
import type { CategorySource } from '../api/client'
import { ApiError } from '../api/client'

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string
  subtitle?: ReactNode
  actions?: ReactNode
}) {
  return (
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      spacing={2}
      sx={{ mb: 3, justifyContent: 'space-between', alignItems: { sm: 'flex-end' } }}
    >
      <Box>
        <Typography variant="h4" component="h1">
          {title}
        </Typography>
        {subtitle && (
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {actions && (
        <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
          {actions}
        </Stack>
      )}
    </Stack>
  )
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  color = 'primary.main',
}: {
  label: string
  value: ReactNode
  hint?: ReactNode
  icon?: ReactNode
  color?: string
}) {
  return (
    <Card>
      <CardContent>
        <Stack direction="row" sx={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
            {label}
          </Typography>
          {icon && <Box sx={{ color, display: 'flex' }}>{icon}</Box>}
        </Stack>
        <Typography variant="h4" sx={{ mt: 1 }}>
          {value}
        </Typography>
        {hint && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {hint}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

const SOURCE_LABEL: Record<CategorySource, string> = {
  line: 'Set on line',
  product: 'Set on product',
  group: 'From group',
  default: 'Default',
}

const SOURCE_COLOR: Record<CategorySource, 'primary' | 'secondary' | 'default' | 'warning'> = {
  line: 'primary',
  product: 'primary',
  group: 'secondary',
  default: 'warning',
}

/** A tax category with where it came from (product, group or default). */
export function CategoryChip({
  code,
  source,
  names,
}: {
  code: string
  source?: CategorySource
  names?: Map<string, string>
}) {
  const name = names?.get(code)
  return (
    <Stack direction="row" spacing={0.75} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
      <Tooltip title={name ?? code}>
        <Chip size="small" label={code} variant="outlined" />
      </Tooltip>
      {source && (
        <Chip
          size="small"
          label={SOURCE_LABEL[source]}
          color={SOURCE_COLOR[source]}
          variant={source === 'default' ? 'outlined' : 'filled'}
        />
      )}
    </Stack>
  )
}

export function ErrorAlert({ error }: { error: unknown }) {
  if (!error) return null
  const message = error instanceof Error ? error.message : 'Something went wrong.'
  return (
    <Alert severity="error" sx={{ mb: 2 }}>
      {message}
      {error instanceof ApiError && error.fieldErrors.length > 0 && (
        <Box component="ul" sx={{ m: 0, pl: 2 }}>
          {error.fieldErrors.map((fieldError) => (
            <li key={fieldError.loc.join('.')}>
              {fieldError.loc.slice(1).join(' › ')}: {fieldError.msg}
            </li>
          ))}
        </Box>
      )}
      {error instanceof ApiError && error.correlationId && (
        <Typography variant="caption" component="div" sx={{ mt: 0.5, opacity: 0.8 }}>
          Correlation ID: {error.correlationId}
        </Typography>
      )}
    </Alert>
  )
}
