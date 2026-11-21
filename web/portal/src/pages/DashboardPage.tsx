import { Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  CardHeader,
  Chip,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { BarChart } from '@mui/x-charts/BarChart'
import { PieChart } from '@mui/x-charts/PieChart'
import CalculateOutlined from '@mui/icons-material/CalculateOutlined'
import Inventory2Outlined from '@mui/icons-material/Inventory2Outlined'
import PublicOutlined from '@mui/icons-material/PublicOutlined'
import ScienceOutlined from '@mui/icons-material/ScienceOutlined'
import CheckCircle from '@mui/icons-material/CheckCircle'
import RadioButtonUnchecked from '@mui/icons-material/RadioButtonUnchecked'
import QueryStatsOutlined from '@mui/icons-material/QueryStatsOutlined'
import TaskAltOutlined from '@mui/icons-material/TaskAltOutlined'
import CategoryOutlined from '@mui/icons-material/CategoryOutlined'
import {
  useJurisdictions,
  useRecentCalculations,
  useSetupSummary,
  useUsageSummary,
} from '../api/hooks'
import { tenantName, useTenant } from '../tenant-context'
import { ErrorAlert, PageHeader, StatCard } from '../components/common'
import { currentMonthLabel, formatDateTime, formatMoney, plural } from '../format'

export function DashboardPage() {
  const { tenant } = useTenant()
  const usage = useUsageSummary()
  const setup = useSetupSummary()
  const jurisdictions = useJurisdictions()

  const summary = usage.data
  const setupData = setup.data
  const successRate =
    summary && summary.requests > 0
      ? `${Math.round((summary.successful / summary.requests) * 100)}%`
      : '—'
  const mappedShare =
    setupData && setupData.products_total > 0
      ? Math.round(
          ((setupData.products_total - setupData.products_by_default) / setupData.products_total) *
            100,
        )
      : 0

  return (
    <>
      <PageHeader
        title={`Welcome, ${tenantName(tenant)}`}
        subtitle={
          summary
            ? `Your tax setup and calculations for ${currentMonthLabel(summary.month)}.`
            : 'Your tax setup and calculations this month.'
        }
        actions={
          <Button
            variant="contained"
            startIcon={<CalculateOutlined />}
            component={RouterLink}
            to="/calculator"
          >
            New calculation
          </Button>
        }
      />
      <ErrorAlert error={usage.error ?? setup.error} />

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard
            label="Calculations this month"
            value={summary ? summary.requests.toLocaleString() : <Skeleton width={60} />}
            hint={
              summary &&
              `${summary.successful} successful · ${summary.rejected + summary.unsupported} not calculated`
            }
            icon={<QueryStatsOutlined />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard
            label="Success rate"
            value={summary ? successRate : <Skeleton width={60} />}
            hint="Requests answered with a tax result"
            icon={<TaskAltOutlined />}
            color="success.main"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard
            label="Products mapped"
            value={setupData ? `${mappedShare}%` : <Skeleton width={60} />}
            hint={
              setupData &&
              `${setupData.products_total - setupData.products_by_default} of ${setupData.products_total} have a category`
            }
            icon={<CategoryOutlined />}
            color="secondary.main"
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
          <StatCard
            label="Countries supported"
            value={jurisdictions.data ? jurisdictions.data.length : <Skeleton width={60} />}
            hint="By the TSG sample calculator"
            icon={<PublicOutlined />}
            color="info.main"
          />
        </Grid>

        <Grid size={12}>
          <QuickLinks unmapped={setupData?.products_by_default ?? 0} />
        </Grid>

        <Grid size={{ xs: 12, lg: 8 }}>
          <Card>
            <CardHeader
              title="Daily calculations"
              subheader={summary ? currentMonthLabel(summary.month) : undefined}
            />
            <CardContent sx={{ pt: 0 }}>
              {summary ? (
                <BarChart
                  height={280}
                  xAxis={[
                    {
                      scaleType: 'band',
                      data: summary.by_day.map((d) => Number(d.day.slice(8))),
                      label: 'Day of month',
                    },
                  ]}
                  series={[
                    {
                      data: summary.by_day.map((d) => d.successful),
                      label: 'Successful',
                      stack: 'total',
                      color: '#3949ab',
                    },
                    {
                      data: summary.by_day.map((d) => d.requests - d.successful),
                      label: 'Not calculated',
                      stack: 'total',
                      color: '#ef9a9a',
                    },
                  ]}
                  yAxis={[
                    {
                      min: 0,
                      max: Math.max(...summary.by_day.map((d) => d.requests)) < 5 ? 5 : undefined,
                      tickMinStep: 1,
                    },
                  ]}
                  margin={{ left: 0, right: 8 }}
                />
              ) : (
                <Skeleton variant="rounded" height={280} />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Card>
            <CardHeader title="Outcomes" subheader="Who responded and how" />
            <CardContent sx={{ pt: 0 }}>
              {summary && summary.requests > 0 ? (
                <>
                  <PieChart
                    height={180}
                    series={[
                      {
                        innerRadius: 50,
                        paddingAngle: 2,
                        cornerRadius: 4,
                        data: [
                          { id: 0, value: summary.successful, label: 'Successful', color: '#3949ab' },
                          { id: 1, value: summary.rejected, label: 'Rejected', color: '#ef9a9a' },
                          {
                            id: 2,
                            value: summary.unsupported,
                            label: 'Unsupported',
                            color: '#ffcc80',
                          },
                        ],
                      },
                    ]}
                  />
                  <Stack spacing={1} sx={{ mt: 2 }}>
                    {summary.by_engine.map((engine) => (
                      <Stack
                        key={engine.engine}
                        direction="row"
                        sx={{ justifyContent: 'space-between', alignItems: 'center' }}
                      >
                        <Chip size="small" label={engine.engine} variant="outlined" />
                        <Typography variant="body2" color="text.secondary">
                          {engine.responded} responded / {engine.requests} requests
                        </Typography>
                      </Stack>
                    ))}
                  </Stack>
                </>
              ) : (
                <EmptyState text="No calculations yet this month." />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <SetupChecklist
            groups={setupData?.groups_total ?? 0}
            products={setupData?.products_total ?? 0}
            unmapped={setupData?.products_by_default ?? 0}
            calculations={summary?.successful ?? 0}
            defaultCategory={setupData?.default_category}
          />
        </Grid>

        <Grid size={{ xs: 12, lg: 8 }}>
          <RecentCalculations />
        </Grid>
      </Grid>
    </>
  )
}

function QuickLinks({ unmapped }: { unmapped: number }) {
  const links = [
    {
      to: '/products',
      icon: <Inventory2Outlined fontSize="large" />,
      title: 'Products & tax categories',
      text: 'Tell us what you sell and how each product is taxed.',
      badge: unmapped > 0 ? `${unmapped} using default` : undefined,
    },
    {
      to: '/calculator',
      icon: <CalculateOutlined fontSize="large" />,
      title: 'Sample calculator',
      text: 'Calculate tax for a sale in any supported country.',
    },
    {
      to: '/calculator?scenario=UK-04',
      icon: <ScienceOutlined fontSize="large" />,
      title: 'Run a test scenario',
      text: 'Load a documented scenario and compare with the expected answer.',
    },
    {
      to: '/tax-rates',
      icon: <PublicOutlined fontSize="large" />,
      title: 'Countries & rates',
      text: 'See how each country taxes each product category.',
    },
  ]
  return (
    <Grid container spacing={2.5}>
      {links.map((link) => (
        <Grid key={link.to} size={{ xs: 12, sm: 6, lg: 3 }}>
          <Card>
            <CardActionArea component={RouterLink} to={link.to} sx={{ height: '100%' }}>
              <CardContent>
                <Stack direction="row" sx={{ justifyContent: 'space-between', mb: 1.5 }}>
                  <Box sx={{ color: 'primary.main', display: 'flex' }}>{link.icon}</Box>
                  {link.badge && <Chip size="small" color="warning" label={link.badge} />}
                </Stack>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {link.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {link.text}
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        </Grid>
      ))}
    </Grid>
  )
}

function SetupChecklist(props: {
  groups: number
  products: number
  unmapped: number
  calculations: number
  defaultCategory?: string
}) {
  const steps = [
    {
      done: Boolean(props.defaultCategory),
      label: 'Default category chosen',
      detail: props.defaultCategory ?? '',
    },
    { done: props.groups > 0, label: 'Product groups mapped', detail: plural(props.groups, 'group') },
    { done: props.products > 0, label: 'Products added', detail: plural(props.products, 'product') },
    {
      done: props.products > 0 && props.unmapped === 0,
      label: 'Every product has a category',
      detail: props.unmapped > 0 ? `${props.unmapped} still on default` : 'All mapped',
    },
    {
      done: props.calculations > 0,
      label: 'First calculation done',
      detail: `${props.calculations} this month`,
    },
  ]
  const done = steps.filter((step) => step.done).length
  return (
    <Card>
      <CardHeader title="Setup progress" subheader={`${done} of ${steps.length} steps complete`} />
      <CardContent sx={{ pt: 0 }}>
        <LinearProgress
          variant="determinate"
          value={(done / steps.length) * 100}
          sx={{ height: 8, borderRadius: 4, mb: 1 }}
        />
        <List dense disablePadding>
          {steps.map((step) => (
            <ListItem key={step.label} disableGutters>
              <ListItemIcon sx={{ minWidth: 36 }}>
                {step.done ? (
                  <CheckCircle color="success" fontSize="small" />
                ) : (
                  <RadioButtonUnchecked color="disabled" fontSize="small" />
                )}
              </ListItemIcon>
              <ListItemText primary={step.label} secondary={step.detail} />
            </ListItem>
          ))}
        </List>
        <Button component={RouterLink} to="/products" size="small" sx={{ mt: 1 }}>
          Continue setup
        </Button>
      </CardContent>
    </Card>
  )
}

function RecentCalculations() {
  const { data, isLoading } = useRecentCalculations()
  return (
    <Card>
      <CardHeader
        title="Recent calculations"
        action={
          <Button component={RouterLink} to="/calculator" size="small">
            Calculate
          </Button>
        }
      />
      {isLoading ? (
        <CardContent>
          <Skeleton variant="rounded" height={200} />
        </CardContent>
      ) : data && data.length > 0 ? (
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>When</TableCell>
                <TableCell>Reference</TableCell>
                <TableCell>Country</TableCell>
                <TableCell align="right">Lines</TableCell>
                <TableCell align="right">Tax</TableCell>
                <TableCell align="right">Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.map((record) => (
                <TableRow key={record.id} hover>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>
                    {formatDateTime(record.created_at)}
                  </TableCell>
                  <TableCell>{record.reference ?? '—'}</TableCell>
                  <TableCell>{record.jurisdiction_name}</TableCell>
                  <TableCell align="right">{record.line_count}</TableCell>
                  <TableCell align="right">{formatMoney(record.tax_total, record.currency)}</TableCell>
                  <TableCell align="right">
                    {formatMoney(record.gross_total, record.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <CardContent>
          <EmptyState text="No calculations yet. Try the sample calculator." />
        </CardContent>
      )}
    </Card>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
      {text}
    </Typography>
  )
}
