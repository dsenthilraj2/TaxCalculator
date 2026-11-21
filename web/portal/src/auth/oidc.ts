import type { AuthProviderProps } from 'react-oidc-context'

/** OIDC settings. The dev IdP locally (tools/dev-idp); Entra External ID later. */
export const oidcConfig: AuthProviderProps = {
  authority: import.meta.env.VITE_OIDC_AUTHORITY ?? 'http://127.0.0.1:8081',
  client_id: import.meta.env.VITE_OIDC_CLIENT_ID ?? 'tsg-portal',
  redirect_uri: `${window.location.origin}/`,
  post_logout_redirect_uri: `${window.location.origin}/`,
  scope: 'openid profile email',
  automaticSilentRenew: false,
  // Remove ?code=&state= from the address bar after signing in.
  onSigninCallback: () => {
    window.history.replaceState({}, document.title, window.location.pathname)
  },
}
