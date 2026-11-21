# TSG Tax Gateway — Portal

React + TypeScript (strict) · Vite · MUI · TanStack Query · React Router.

```bash
npm ci          # or: make web-install
npm run dev     # http://127.0.0.1:5173, proxies /v1 and /health to the API on :8000
```

- `src/api/schema.d.ts` is generated from `backend/openapi.json` (`make openapi`). Don't edit it by hand.
- `src/api/client.ts` adds the `X-TSG-Tenant` header and turns problem-details errors into `ApiError`.
- Pages: `src/pages/` (Dashboard, Products & tax categories, Sample calculator, Countries & rates).
- Checks: `make web-check` (tsc, oxlint, vitest).
