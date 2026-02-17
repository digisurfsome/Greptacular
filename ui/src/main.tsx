import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { StylePreviewPage } from './components/StylePreviewPage'
import { QuadPreviewPage } from './components/QuadPreviewPage'
import { WorkspacePage } from './pages/WorkspacePage'
import { isStylePreviewRoute, isQuadPreviewRoute, isWorkspaceRoute } from './lib/routes'
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
 * - /#/workspace → IdeaForge Workspace
 * - Everything else → Main App
 */
function Root() {
  // Track hash changes so route switches trigger re-renders
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash)
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // Use hash in conditions to satisfy the linter (referential dependency)
  if (hash.startsWith('#/style-preview/') && isStylePreviewRoute()) {
    return <StylePreviewPage />
  }
  if (hash.startsWith('#/quad-preview/') && isQuadPreviewRoute()) {
    return <QuadPreviewPage />
  }
  if ((hash === '#/workspace' || hash.startsWith('#/workspace/')) && isWorkspaceRoute()) {
    return <WorkspacePage />
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
