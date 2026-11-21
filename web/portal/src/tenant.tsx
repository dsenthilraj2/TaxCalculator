import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { setApiTenant } from './api/client'
import { TenantContext } from './tenant-context'

const STORAGE_KEY = 'tsg.tenant'

function readStoredTenant(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) ?? 'acme'
  } catch {
    return 'acme'
  }
}

/** Provides the selected client. Dev-only until OIDC login provides the tenant from the token. */
export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState(() => {
    const initial = readStoredTenant()
    setApiTenant(initial)
    return initial
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, tenant)
    } catch {
      // Storage can be unavailable (private mode); the selection still works for this session.
    }
  }, [tenant])

  const value = useMemo(
    () => ({
      tenant,
      setTenant: (next: string) => {
        setApiTenant(next)
        setTenantState(next)
      },
    }),
    [tenant],
  )
  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>
}
