import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { StylePreviewPage } from './components/StylePreviewPage'
import { QuadPreviewPage } from './components/QuadPreviewPage'
import { isStylePreviewRoute, isQuadPreviewRoute } from './lib/routes'
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
})

/**
 * Route-based rendering:
 * - /#/style-preview/:styleId/:page → Standalone single-page preview (for screenshots)
 * - /#/quad-preview/:styleId → Quad view (all 4 pages at once)
 * - Everything else → Main App
 */
function Root() {
  if (isStylePreviewRoute()) {
    return <StylePreviewPage />
  }
  if (isQuadPreviewRoute()) {
    return <QuadPreviewPage />
  }
  return <App />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <Root />
    </QueryClientProvider>
  </StrictMode>,
)
