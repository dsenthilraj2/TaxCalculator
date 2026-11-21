import { useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Alert, Box } from '@mui/material'
import { api, setApiTenant, unwrap } from './api/client'
import { TenantContext } from './tenant-context'
import { FullPageSpinner } from './auth/AuthGate'

const STORAGE_KEY = 'tsg.staffTenant'

function readStoredTenant(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

function storeTenant(tenant: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, tenant)
  } catch {
    // Storage can be unavailable (private mode); the choice still works for this session.
  }
}

/**
 * Loads the signed-in user and decides which client the app acts for.
 * Client users act for the client in their token; TSG staff pick one (remembered locally).
 */
export function TenantProvider({ children }: { children: ReactNode }) {
  const meQuery = useQuery({
    queryKey: ['me'],
    queryFn: async () => unwrap(await api.GET('/v1/me')),
    staleTime: Infinity,
  })
  const [staffChoice, setStaffChoice] = useState<string | null>(readStoredTenant)
  const me = meQuery.data

  const value = useMemo(() => {
    if (!me) return null
    const tenant = me.is_tsg_staff
      ? staffChoice && me.tenants.includes(staffChoice)
        ? staffChoice
        : (me.tenants[0] ?? '')
      : (me.tenant_id ?? '')
    // Must be set before children render so their first requests carry the right client.
    setApiTenant(me.is_tsg_staff ? tenant : '')
    return {
      tenant,
      me,
      setTenant: (next: string) => {
        if (!me.is_tsg_staff) return
        setApiTenant(next)
        storeTenant(next)
        setStaffChoice(next)
      },
    }
  }, [me, staffChoice])

  if (meQuery.error) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="error">Could not load your account: {meQuery.error.message}</Alert>
      </Box>
    )
  }
  if (!value) return <FullPageSpinner label="Loading your account…" />
  if (!value.tenant) {
    return (
      <Box sx={{ p: 4 }}>
        <Alert severity="warning">Your account is not linked to any client yet.</Alert>
      </Box>
    )
  }
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>
}
