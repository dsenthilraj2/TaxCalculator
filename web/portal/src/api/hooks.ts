import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useTenant } from '../tenant-context'
import {
  api,
  unwrap,
  type CalculateRequest,
  type GroupMapping,
  type Scenario,
  type Schemas,
} from './client'

type ProductStatus = 'all' | 'mapped' | 'unmapped'

// ------------------------------------------------------------------ reference data
export function useTaxCategories() {
  return useQuery({
    queryKey: ['tax-categories'],
    queryFn: async () => unwrap(await api.GET('/v1/tax-categories')),
    staleTime: Infinity,
  })
}

export function useJurisdictions() {
  return useQuery({
    queryKey: ['jurisdictions'],
    queryFn: async () => unwrap(await api.GET('/v1/tax/jurisdictions')),
    staleTime: Infinity,
  })
}

export function useScenarios() {
  return useQuery({
    queryKey: ['scenarios'],
    queryFn: async () => unwrap(await api.GET('/v1/dev/scenarios')) as unknown as Scenario[],
    staleTime: Infinity,
  })
}

export function useDevTenants() {
  return useQuery({
    queryKey: ['dev-tenants'],
    queryFn: async () => unwrap(await api.GET('/v1/dev/tenants')),
    staleTime: Infinity,
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ['health-ready'],
    queryFn: async () => {
      const response = await fetch('/health/ready')
      return (await response.json()) as Schemas['ReadinessResponse']
    },
    refetchInterval: 30_000,
  })
}

// ------------------------------------------------------------------ tenant data
export function useSetupSummary() {
  const { tenant } = useTenant()
  return useQuery({
    queryKey: [tenant, 'setup-summary'],
    queryFn: async () => unwrap(await api.GET('/v1/tax-setup/summary')),
    enabled: Boolean(tenant),
  })
}

export function useProducts(filters: { search?: string; category?: string; status: ProductStatus }) {
  const { tenant } = useTenant()
  return useQuery({
    queryKey: [tenant, 'products', filters],
    queryFn: async () =>
      unwrap(
        await api.GET('/v1/products', {
          params: {
            query: {
              search: filters.search || undefined,
              tax_category: filters.category || undefined,
              status: filters.status,
            },
          },
        }),
      ),
    enabled: Boolean(tenant),
    placeholderData: (previous) => previous,
  })
}

export function useGroups() {
  const { tenant } = useTenant()
  return useQuery({
    queryKey: [tenant, 'groups'],
    queryFn: async () => unwrap(await api.GET('/v1/product-groups')),
    enabled: Boolean(tenant),
  })
}

export function useTaxSettings() {
  const { tenant } = useTenant()
  return useQuery({
    queryKey: [tenant, 'tax-settings'],
    queryFn: async () => unwrap(await api.GET('/v1/tax-settings')),
    enabled: Boolean(tenant),
  })
}

export function useUsageSummary(month?: string) {
  const { tenant } = useTenant()
  return useQuery({
    queryKey: [tenant, 'usage', month ?? 'current'],
    queryFn: async () =>
      unwrap(await api.GET('/v1/usage/summary', { params: { query: { month } } })),
    enabled: Boolean(tenant),
  })
}

export function useRecentCalculations(limit = 8) {
  const { tenant } = useTenant()
  return useQuery({
    queryKey: [tenant, 'recent-calculations', limit],
    queryFn: async () =>
      unwrap(await api.GET('/v1/calculations/recent', { params: { query: { limit } } })),
    enabled: Boolean(tenant),
  })
}

// ------------------------------------------------------------------ mutations
/** Invalidate everything that belongs to the current client after a change. */
function useInvalidateTenant() {
  const queryClient = useQueryClient()
  const { tenant } = useTenant()
  return () => queryClient.invalidateQueries({ queryKey: [tenant] })
}

export function useSaveProduct() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (product: Schemas['Product']) => {
      const { sku, ...body } = product
      return unwrap(
        await api.PUT('/v1/products/{sku}', { params: { path: { sku } }, body }),
      )
    },
    onSuccess: invalidate,
  })
}

export function useDeleteProduct() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (sku: string) =>
      unwrap(await api.DELETE('/v1/products/{sku}', { params: { path: { sku } } })),
    onSuccess: invalidate,
  })
}

export function useImportProducts() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (products: Schemas['Product'][]) =>
      unwrap(await api.POST('/v1/products/import', { body: products })),
    onSuccess: invalidate,
  })
}

export function useSaveGroup() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (mapping: GroupMapping) =>
      unwrap(
        await api.PUT('/v1/product-groups/{group}', {
          params: { path: { group: mapping.group } },
          body: { tax_category: mapping.tax_category },
        }),
      ),
    onSuccess: invalidate,
  })
}

export function useDeleteGroup() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (group: string) =>
      unwrap(await api.DELETE('/v1/product-groups/{group}', { params: { path: { group } } })),
    onSuccess: invalidate,
  })
}

export function useSaveTaxSettings() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (defaultCategory: string) =>
      unwrap(await api.PUT('/v1/tax-settings', { body: { default_category: defaultCategory } })),
    onSuccess: invalidate,
  })
}

export function useCalculate() {
  const invalidate = useInvalidateTenant()
  return useMutation({
    mutationFn: async (request: CalculateRequest) =>
      unwrap(await api.POST('/v1/tax/calculate', { body: request })),
    onSettled: invalidate,
  })
}
