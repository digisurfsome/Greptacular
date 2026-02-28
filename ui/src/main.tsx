import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { StylePreviewPage } from './components/StylePreviewPage'
import { QuadPreviewPage } from './components/QuadPreviewPage'
import { WorkspacePage } from './pages/WorkspacePage'
import { RoleLibraryPage } from './pages/RoleLibraryPage'
import { DunkStackPage } from './pages/DunkStackPage'
import { DashboardPage } from './pages/DashboardPage'
import { YTStrategyLabPage } from './pages/YTStrategyLabPage'
import { ErrorBoundary } from './components/ErrorBoundary'
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
 * - /#/dunkstack → DunkStack Context Mechanism
 * - Everything else → Main App
 */
function Root() {
  const [hash, setHash] = useState(window.location.hash)

  useEffect(() => {
    const handler = () => setHash(window.location.hash)
    window.addEventListener('hashchange', handler)
    return () => window.removeEventListener('hashchange', handler)
  }, [])

  if (hash.startsWith('#/style-preview/')) {
    return <StylePreviewPage />
  }
  if (hash.startsWith('#/quad-preview/')) {
    return <QuadPreviewPage />
  }
  if (hash === '#/dunkstack' || hash.startsWith('#/dunkstack/')) {
    return <DunkStackPage />
  }
  if (hash === '#/workspace' || hash.startsWith('#/workspace/')) {
    return <ErrorBoundary><WorkspacePage /></ErrorBoundary>
  }
  if (hash === '#/roles' || hash.startsWith('#/roles/')) {
    return <RoleLibraryPage />
  }
  if (hash === '#/dashboard' || hash.startsWith('#/dashboard/')) {
    return <DashboardPage />
  }
  if (hash === '#/yt-lab' || hash.startsWith('#/yt-lab/')) {
    return <YTStrategyLabPage />
  }
  return <App />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Root />
      </ErrorBoundary>
    </QueryClientProvider>
  </StrictMode>,
)
