import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  AppBar,
  Avatar,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
} from '@mui/material'
import { useColorScheme, useTheme } from '@mui/material/styles'
import { useAuth } from 'react-oidc-context'
import { useQueryClient } from '@tanstack/react-query'
import LogoutOutlined from '@mui/icons-material/LogoutOutlined'
import DashboardOutlined from '@mui/icons-material/DashboardOutlined'
import Inventory2Outlined from '@mui/icons-material/Inventory2Outlined'
import CalculateOutlined from '@mui/icons-material/CalculateOutlined'
import PublicOutlined from '@mui/icons-material/PublicOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import DarkModeOutlined from '@mui/icons-material/DarkModeOutlined'
import LightModeOutlined from '@mui/icons-material/LightModeOutlined'
import ReceiptLongOutlined from '@mui/icons-material/ReceiptLongOutlined'
import { tenantName, useTenant } from '../tenant-context'
import { useHealth } from '../api/hooks'

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
          <UserMenu />
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
  const { tenant, setTenant, me } = useTenant()
  if (!me.is_tsg_staff) {
    return <Chip label={tenantName(tenant)} variant="outlined" sx={{ fontWeight: 600 }} />
  }
  return (
    <TextField
      select
      size="small"
      label="Acting for client"
      value={me.tenants.includes(tenant) ? tenant : ''}
      onChange={(event) => setTenant(event.target.value)}
      sx={{ minWidth: 190 }}
    >
      {me.tenants.map((id) => (
        <MenuItem key={id} value={id}>
          {tenantName(id)}
        </MenuItem>
      ))}
    </TextField>
  )
}

function UserMenu() {
  const { me } = useTenant()
  const auth = useAuth()
  const queryClient = useQueryClient()
  const [anchor, setAnchor] = useState<HTMLElement | null>(null)
  const label = me.name ?? me.email ?? me.subject
  const initials = label
    .split(/[\s@.]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')

  const signOut = () => {
    setAnchor(null)
    queryClient.clear()
    void auth.signoutRedirect()
  }

  return (
    <>
      <Tooltip title={label}>
        <IconButton onClick={(event) => setAnchor(event.currentTarget)} aria-label="Account">
          <Avatar sx={{ width: 32, height: 32, fontSize: 14, bgcolor: 'primary.main' }}>
            {initials}
          </Avatar>
        </IconButton>
      </Tooltip>
      <Menu
        anchorEl={anchor}
        open={Boolean(anchor)}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Box sx={{ px: 2, py: 1, minWidth: 240 }}>
          <Typography variant="subtitle2">{me.name ?? me.subject}</Typography>
          {me.email && (
            <Typography variant="body2" color="text.secondary">
              {me.email}
            </Typography>
          )}
          <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap' }} useFlexGap>
            {me.roles.map((role) => (
              <Chip key={role} size="small" label={role} />
            ))}
            {!me.can_edit_setup && <Chip size="small" variant="outlined" label="Read-only" />}
          </Stack>
        </Box>
        <Divider />
        <MenuItem onClick={signOut}>
          <ListItemIcon>
            <LogoutOutlined fontSize="small" />
          </ListItemIcon>
          Sign out
        </MenuItem>
      </Menu>
    </>
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
  const identity = data?.checks.find((check) => check.name === 'identity-provider')
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
          sx={{ mr: 1 }}
        />
      )}
      {identity && (
        <Chip
          size="small"
          variant="outlined"
          color={identity.ok ? 'success' : 'error'}
          label="Identity"
          sx={{ mt: 1 }}
        />
      )}
    </Box>
  )
}
