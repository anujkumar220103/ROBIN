// Login page — authenticates the user and redirects to dashboard on success.

import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Bot } from 'lucide-react'
import Input from '../components/common/Input.jsx'
import Button from '../components/common/Button.jsx'
import { useAuth } from '../hooks/useAuth.js'

function getErrorMessage(err) {
  if (err.response?.status === 401) return 'Invalid email or password.'
  if (err.response?.data?.detail) return err.response.data.detail
  if (err.message === 'Network Error') return 'Unable to reach the server. Please check your connection.'
  return 'Login failed. Please try again.'
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()

  // Redirect to original page after login, or dashboard by default.
  const from = location.state?.from?.pathname || '/dashboard'

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
    if (serverError) setServerError('')
  }

  function validate() {
    const e = {}
    if (!form.email.trim()) e.email = 'Email is required.'
    if (!form.password) e.password = 'Password is required.'
    return e
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setServerError('')

    const validationErrors = validate()
    if (Object.keys(validationErrors).length) {
      setErrors(validationErrors)
      return
    }

    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate(from, { replace: true })
    } catch (err) {
      setServerError(getErrorMessage(err))
      // Keep email but clear password on failure
      setForm((prev) => ({ ...prev, password: '' }))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-96 bg-accent flex-col justify-center px-10 py-12">
        <div className="flex items-center gap-2 mb-10">
          <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
            <Bot size={18} className="text-white" />
          </div>
          <span className="text-white font-bold text-base">ROBIN AI</span>
        </div>
        <h2 className="text-white text-2xl font-bold mb-3">Welcome back</h2>
        <p className="text-white/70 text-sm leading-relaxed">
          Sign in to your company dashboard to manage your knowledge base and chatbot configuration.
        </p>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
              <Bot size={15} className="text-white" />
            </div>
            <span className="text-sm font-bold text-primary-text">ROBIN AI</span>
          </div>

          <h1 className="text-xl font-bold text-primary-text mb-1">Sign in to your account</h1>
          <p className="text-sm text-secondary-text mb-6">
            New to ROBIN AI?{' '}
            <Link to="/register" className="text-accent font-medium hover:underline">Create an account</Link>
          </p>

          {serverError && (
            <div role="alert" className="mb-4 px-4 py-3 rounded-lg bg-error/10 border border-error/20 text-sm text-error">
              {serverError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <Input
              id="email"
              name="email"
              type="email"
              label="Email address"
              placeholder="you@company.com"
              value={form.email}
              onChange={handleChange}
              error={errors.email}
              autoComplete="email"
              disabled={loading}
            />
            <Input
              id="password"
              name="password"
              type="password"
              label="Password"
              placeholder="Your password"
              value={form.password}
              onChange={handleChange}
              error={errors.password}
              autoComplete="current-password"
              disabled={loading}
            />

            <Button type="submit" loading={loading} disabled={loading} className="w-full mt-2">
              Sign in
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
