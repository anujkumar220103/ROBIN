// Root application component — sets up routing and authentication context.

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.jsx'
import ProtectedRoute from './routes/ProtectedRoute.jsx'
import PublicRoute from './routes/PublicRoute.jsx'
import DashboardLayout from './components/layout/DashboardLayout.jsx'
import WidgetErrorBoundary from './components/widget/WidgetErrorBoundary.jsx'

import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import DocumentsPage from './pages/DocumentsPage.jsx'
import PlaygroundPage from './pages/PlaygroundPage.jsx'
import ChatbotSettingsPage from './pages/ChatbotSettingsPage.jsx'
import IntegrationPage from './pages/IntegrationPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import WidgetPage from './pages/WidgetPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ----------------------------------------------------------------
            Widget route — rendered outside AuthProvider intentionally.
            The embedded chatbot is a fully public page; it must never fire
            GET /auth/me or attach auth cookies, both of which would be
            blocked in a cross-origin iframe and cause a 15-second stall
            (Axios timeout) followed by a React state-update crash on an
            effectively-unmounted component tree.
        ---------------------------------------------------------------- */}
        <Route
          path="/widget/:publicId"
          element={
            <WidgetErrorBoundary>
              <WidgetPage />
            </WidgetErrorBoundary>
          }
        />

        {/* All other routes share the AuthProvider context */}
        <Route
          path="/*"
          element={
            <AuthProvider>
              <Routes>
                {/* Public routes */}
                <Route path="/" element={<LandingPage />} />
                <Route
                  path="/login"
                  element={<PublicRoute><LoginPage /></PublicRoute>}
                />
                <Route
                  path="/register"
                  element={<PublicRoute><RegisterPage /></PublicRoute>}
                />

                {/* Protected dashboard routes */}
                <Route
                  path="/dashboard"
                  element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}
                >
                  <Route index element={<DashboardPage />} />
                  <Route path="documents" element={<DocumentsPage />} />
                  <Route path="playground" element={<PlaygroundPage />} />
                  <Route path="chatbot-settings" element={<ChatbotSettingsPage />} />
                  <Route path="integration" element={<IntegrationPage />} />
                  <Route path="profile" element={<ProfilePage />} />
                </Route>

                {/* 404 */}
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </AuthProvider>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
