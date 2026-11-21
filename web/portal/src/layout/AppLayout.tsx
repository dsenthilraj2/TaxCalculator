import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  AppBar,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material'
import { useColorScheme, useTheme } from '@mui/material/styles'
import DashboardOutlined from '@mui/icons-material/DashboardOutlined'
import Inventory2Outlined from '@mui/icons-material/Inventory2Outlined'
import CalculateOutlined from '@mui/icons-material/CalculateOutlined'
import PublicOutlined from '@mui/icons-material/PublicOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import DarkModeOutlined from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlined from '@mui/icons-material/LightModeOutlined'
import ReceiptLongOutlined from '@mui/icons-material/ReceiptLongOutlined'
import { tenantName, useTenant } from '../tenant-context'
import { useDevTenants, useHealth } from '../api/hooks'

const DRAWER_WIDTH = 248

const NAV = [
  { to: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
  { to: '/products', label: 'Products & tax categories', icon: <Inventory2Outlined /> },
  { to: '/calculator', label: 'Sample calculator', icon: <CalculateOutlined /> },
  { to: '/tax-rates', label: 'Countries & rates', icon: <PublicOutlined /> },
]

export function AppLayout() {
  const theme = useTheme()
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'))
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  // Start each page at the top instead of keeping the previous page's scroll position.
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ gap: 1.5 }}>
        <ReceiptLongOutlined color="primary" />
        <Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            TSG Tax Gateway
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Local development
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      <List sx={{ px: 1, py: 1.5 }}>
        {NAV.map((item) => {
          const selected =
            item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to)
          return (
            <ListItemButton
              key={item.to}
              component={NavLink}
              to={item.to}
              selected={selected}
              onClick={() => setMobileOpen(false)}
              sx={{ borderRadius: 2, mb: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} slotProps={{ primary: { variant: 'body2' } }} />
            </ListItemButton>
          )
        })}
      </List>
      <Box sx={{ flexGrow: 1 }} />
      <HealthStatus />
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        color="inherit"
        elevation={0}
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          {!isDesktop && (
            <IconButton edge="start" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <MenuIcon />
            </IconButton>
          )}
          <Box sx={{ flexGrow: 1 }} />
          <TenantPicker />
          <ColorModeToggle />
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        <Drawer
          variant={isDesktop ? 'permanent' : 'temporary'}
          open={isDesktop || mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}
        >
          {drawer}
        </Drawer>
      </Box>

      <Box component="main" sx={{ flexGrow: 1, minWidth: 0, p: { xs: 2, sm: 3 } }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  )
}

function TenantPicker() {
  const { tenant, setTenant } = useTenant()
  const { data: tenants = [tenant] } = useDevTenants()
  // Development only: choose which client you are acting as (replaced by OIDC login later).
  return (
    <TextField
      select
      size="small"
      label="Client (dev only)"
      value={tenants.includes(tenant) ? tenant : ''}
      onChange={(event) => setTenant(event.target.value)}
      sx={{ minWidth: 180 }}
    >
      {tenants.map((id) => (
        <MenuItem key={id} value={id}>
          {tenantName(id)}
        </MenuItem>
      ))}
    </TextField>
  )
}

function ColorModeToggle() {
  const { mode, systemMode, setMode } = useColorScheme()
  const effective = mode === 'system' ? systemMode : mode
  const next = effective === 'dark' ? 'light' : 'dark'
  return (
    <Tooltip title={`Switch to ${next} mode`}>
      <IconButton onClick={() => setMode(next)} aria-label={`Switch to ${next} mode`}>
        {effective === 'dark' ? <LightModeOutlined /> : <DarkModeOutlined />}
      </IconButton>
    </Tooltip>
  )
}

function HealthStatus() {
  const { data, isError } = useHealth()
  const ready = data?.status === 'ready' && !isError
  const database = data?.checks.find((check) => check.name === 'mongodb')
  return (
    <Box sx={{ p: 2 }}>
      <Chip
        size="small"
        variant="outlined"
        color={ready ? 'success' : 'error'}
        label={ready ? 'API ready' : 'API not ready'}
        sx={{ mr: 1 }}
      />
      {database && (
        <Chip
          size="small"
          variant="outlined"
          color={database.ok ? 'success' : 'error'}
          label="MongoDB"
        />
      )}
    </Box>
  )
}
