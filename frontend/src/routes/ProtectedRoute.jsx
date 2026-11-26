// Redirects unauthenticated users to /login before showing protected pages.

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.js'
import LoadingSpinner from '../components/common/LoadingSpinner.jsx'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isInitializing } = useAuth()
  const location = useLocation()

  // Session restore hone tak wait karo — otherwise valid session flash karegi login page.
  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    // Redirect with current path so user returns after login.
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
