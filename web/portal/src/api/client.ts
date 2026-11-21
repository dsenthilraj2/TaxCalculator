import createClient, { type Middleware } from 'openapi-fetch'
import type { components, paths } from './schema'

export type Schemas = components['schemas']
export type ProductView = Schemas['ProductView']
export type GroupMapping = Schemas['GroupMapping']
export type TaxCategory = Schemas['TaxCategory']
export type SetupSummary = Schemas['SetupSummary']
export type UsageSummary = Schemas['UsageSummary']
export type CalculationRecord = Schemas['CalculationRecord']
export type CalculateRequest = Schemas['CalculateRequest']
export type CalculateResponse = Schemas['CalculateResponse']
export type JurisdictionInfo = Schemas['JurisdictionInfo']
export type CategorySource = ProductView['category_source']

/** A test scenario from spec/tax-reference/test-scenarios.md (GET /v1/dev/scenarios). */
export interface Scenario {
  id: string
  group: string
  title: string
  request: CalculateRequest
  expected:
    | { status: 200; tax_total: string; gross_total: string }
    | { status: 422; problem_type: string }
}

/** RFC 9457 problem details returned by the API. */
export class ApiError extends Error {
  readonly status: number
  readonly problemType: string
  readonly correlationId?: string
  readonly fieldErrors: { loc: (string | number)[]; msg: string }[]

  constructor(status: number, body: unknown) {
    const problem = (body ?? {}) as {
      title?: string
      detail?: string
      type?: string
      correlationId?: string
      errors?: { loc: (string | number)[]; msg: string }[]
    }
    super(problem.detail ?? problem.title ?? `Request failed (${status})`)
    this.status = status
    this.problemType = problem.type ?? 'about:blank'
    this.correlationId = problem.correlationId
    this.fieldErrors = problem.errors ?? []
  }
}

export type Me = Schemas['Me']

/** Fired when the API rejects the access token, so the app can ask the user to sign in. */
export const UNAUTHORIZED_EVENT = 'tsg:unauthorized'

let accessToken = ''
let staffTenant = ''

/** Called by the auth gate whenever the signed-in user's token changes. */
export function setApiToken(token: string): void {
  accessToken = token
}

/** TSG staff choose a client per request; client users act for the client in their token. */
export function setApiTenant(tenant: string): void {
  staffTenant = tenant
}

const authHeaders: Middleware = {
  onRequest({ request }) {
    if (accessToken) request.headers.set('Authorization', `Bearer ${accessToken}`)
    if (staffTenant) request.headers.set('X-TSG-Tenant', staffTenant)
    return request
  },
}

export const api = createClient<paths>({ baseUrl: '' })
api.use(authHeaders)

/** Unwrap an openapi-fetch result: return data or throw ApiError. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || !result.response.ok) {
    if (result.response.status === 401) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    throw new ApiError(result.response.status, result.error)
  }
  return result.data as T
}
