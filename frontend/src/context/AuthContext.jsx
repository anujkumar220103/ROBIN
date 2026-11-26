// Manages authentication state across the React application.
// Context API se authentication state sabhi components mein share hoti hai.

import { createContext, useCallback, useEffect, useState } from 'react'
import { authService } from '../services/authService.js'
import { setCsrfToken, clearCsrfToken } from '../services/api.js'

// Context aur Provider ek hi file mein hain — standard React pattern.
// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [company, setCompany] = useState(null)

  // isInitializing: true while checking session on app start
  // Loading ke dauran dashboard flash nahi karna chahte.
  const [isInitializing, setIsInitializing] = useState(true)

  const [initError, setInitError] = useState(null)

  // Restore session when app loads — checks for valid auth cookie.
  // /auth/me now returns csrf_token in the response body so that the
  // in-memory CSRF store is repopulated after a page refresh.
  const restoreSession = useCallback(async () => {
    setIsInitializing(true)
    setInitError(null)
    try {
      const data = await authService.getMe()
      setCsrfToken(data.csrf_token)
      setUser(data.user)
      setCompany(data.company)
    } catch (err) {
      if (err.response?.status === 401) {
        // No valid session — that's normal for logged-out users.
        clearCsrfToken()
        setUser(null)
        setCompany(null)
      } else {
        // Network error or server down — session unknown, track the error.
        setInitError('Unable to reach server. Please check your connection.')
      }
    } finally {
      setIsInitializing(false)
    }
  }, [])

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  const login = useCallback(async (email, password) => {
    const data = await authService.login(email, password)
    // Store CSRF token from response body — cannot read it from document.cookie
    // when the backend is on a different origin (e.g. Render vs. Vercel).
    setCsrfToken(data.csrf_token)
    setUser(data.user)
    setCompany(data.company)
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await authService.logout()
    } catch {
      // Logout attempt fail ho to bhi local state clear karo.
    }
    // Always clear the in-memory CSRF token on logout regardless of API result.
    clearCsrfToken()
    setUser(null)
    setCompany(null)
  }, [])

  const updateUserProfile = useCallback((updatedUser) => {
    setUser(updatedUser)
  }, [])

  const updateCompanyProfile = useCallback((updatedCompany) => {
    setCompany(updatedCompany)
  }, [])

  const isAuthenticated = Boolean(user)

  return (
    <AuthContext.Provider
      value={{
        user,
        company,
        isInitializing,
        initError,
        isAuthenticated,
        login,
        logout,
        restoreSession,
        updateUserProfile,
        updateCompanyProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
