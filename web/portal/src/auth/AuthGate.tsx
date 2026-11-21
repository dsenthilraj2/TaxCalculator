import { useEffect, type ReactNode } from 'react'
import { useAuth } from 'react-oidc-context'
import { useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Typography,
} from '@mui/material'
import LoginOutlined from '@mui/icons-material/LoginOutlined'
import ReceiptLongOutlined from '@mui/icons-material/ReceiptLongOutlined'
import { UNAUTHORIZED_EVENT, setApiToken } from '../api/client'

/** Renders children only for a signed-in user; otherwise shows the sign-in screen. */
export function AuthGate({ children }: { children: ReactNode }) {
  const auth = useAuth()
  const queryClient = useQueryClient()

  // The API rejected the token (expired or revoked): forget it and show sign-in.
  useEffect(() => {
    const onUnauthorized = () => {
      void auth.removeUser()
      queryClient.clear()
    }
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [auth, queryClient])

  if (auth.isLoading || auth.activeNavigator) {
    return <FullPageSpinner label="Signing in…" />
  }
  const user = auth.user
  if (!auth.isAuthenticated || !user || user.expired) {
    setApiToken('')
    return <SignInScreen error={auth.error?.message} onSignIn={() => void auth.signinRedirect()} />
  }
  setApiToken(user.access_token)
  return <>{children}</>
}

export function FullPageSpinner({ label }: { label: string }) {
  return (
    <Stack sx={{ minHeight: '100vh', alignItems: 'center', justifyContent: 'center' }} spacing={2}>
      <CircularProgress />
      <Typography color="text.secondary">{label}</Typography>
    </Stack>
  )
}

function SignInScreen({ error, onSignIn }: { error?: string; onSignIn: () => void }) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        p: 2,
        bgcolor: 'background.default',
      }}
    >
      <Card sx={{ maxWidth: 440, width: '100%', height: 'auto' }}>
        <CardContent sx={{ p: 4 }}>
          <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center', mb: 3 }}>
            <ReceiptLongOutlined color="primary" fontSize="large" />
            <Box>
              <Typography variant="h5">TSG Tax Gateway</Typography>
              <Typography variant="body2" color="text.secondary">
                Tax setup, calculation and usage
              </Typography>
            </Box>
          </Stack>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Sign-in failed: {error}
            </Alert>
          )}
          <Button
            variant="contained"
            size="large"
            fullWidth
            startIcon={<LoginOutlined />}
            onClick={onSignIn}
          >
            Sign in
          </Button>
          <Typography variant="caption" color="text.secondary" component="p" sx={{ mt: 2 }}>
            Local development signs in through the TSG dev identity provider, where you pick a test
            user. Production will use the organisation's identity provider.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  )
}
