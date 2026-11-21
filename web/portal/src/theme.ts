import { createTheme } from '@mui/material/styles'

export const theme = createTheme({
  cssVariables: { colorSchemeSelector: 'class' },
  colorSchemes: {
    light: {
      palette: {
        primary: { main: '#3949ab' },
        secondary: { main: '#00897b' },
        background: { default: '#f5f6fa', paper: '#ffffff' },
      },
    },
    dark: {
      palette: {
        primary: { main: '#8c9eff' },
        secondary: { main: '#4db6ac' },
        background: { default: '#0f1117', paper: '#181b24' },
      },
    },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: '"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    h4: { fontWeight: 700, letterSpacing: '-0.02em' },
    h5: { fontWeight: 700, letterSpacing: '-0.01em' },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  components: {
    MuiCard: {
      defaultProps: { variant: 'outlined' },
      styleOverrides: { root: { height: '100%' } },
    },
    MuiTableCell: {
      styleOverrides: { head: { fontWeight: 600, whiteSpace: 'nowrap' } },
    },
    MuiChip: { styleOverrides: { root: { fontWeight: 500 } } },
  },
})
