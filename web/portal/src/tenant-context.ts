import { createContext, useContext } from 'react'

export interface TenantContextValue {
  tenant: string
  setTenant: (tenant: string) => void
}

export const TenantContext = createContext<TenantContextValue | null>(null)

/** The selected client (dev-only picker until OIDC login provides it). */
export function useTenant(): TenantContextValue {
  const context = useContext(TenantContext)
  if (!context) throw new Error('useTenant must be used inside TenantProvider')
  return context
}

const TENANT_NAMES: Record<string, string> = { acme: 'Acme Pty Ltd', beta: 'Beta Trading' }

/** Display name for a client id. */
export function tenantName(tenant: string): string {
  return TENANT_NAMES[tenant] ?? tenant
}
