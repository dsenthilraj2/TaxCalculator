import { createContext, useContext } from 'react'
import type { Me } from './api/client'

export interface TenantContextValue {
  /** The client currently acted for. */
  tenant: string
  /** Only TSG staff can switch client. */
  setTenant: (tenant: string) => void
  /** The signed-in user (from GET /v1/me). */
  me: Me
}

export const TenantContext = createContext<TenantContextValue | null>(null)

/** The signed-in user and the client they are acting for. */
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
