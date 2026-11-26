// Login page — authenticates the user and redirects to dashboard on success.

import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Bot, Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react'
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

  const from = location.state?.from?.pathname || '/dashboard'

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

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
      setForm((prev) => ({ ...prev, password: '' }))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-[420px] bg-accent flex-col justify-between px-10 py-10 relative overflow-hidden">
        {/* Subtle geometric background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full bg-white -translate-x-1/2 translate-y-1/2" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-2.5 mb-12">
            <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center">
              <Bot size={20} className="text-white" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-white font-bold text-base">ROBIN AI</span>
              <span className="text-white/60 text-[9px] font-medium">Retrieval-Oriented Bot for Intelligent Navigation</span>
            </div>
          </div>

          <h2 className="text-white text-3xl font-bold mb-4 leading-tight">
            Welcome<br />back
          </h2>
          <p className="text-white/70 text-sm leading-relaxed">
            Sign in to your company dashboard and manage your knowledge base, chatbot settings, and document library.
          </p>
        </div>

        {/* Feature highlights */}
        <div className="relative z-10 space-y-3">
          {[
            'Instant answers from your documents',
            'Full company data isolation',
            'Embed on any website in minutes',
          ].map((item) => (
            <div key={item} className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center shrink-0">
                <ArrowRight size={11} className="text-white" />
              </div>
              <span className="text-white/80 text-xs">{item}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-background">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-10 lg:hidden">
            <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-bold text-primary-text">ROBIN AI</span>
              <span className="text-[9px] text-secondary-text font-medium">Retrieval-Oriented Bot for Intelligent Navigation</span>
            </div>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-primary-text mb-1.5">Sign in</h1>
            <p className="text-sm text-secondary-text">
              Don't have an account?{' '}
              <Link to="/register" className="text-accent font-semibold hover:underline">
                Create one free
              </Link>
            </p>
          </div>

          {serverError && (
            <div role="alert" className="mb-5 px-4 py-3 rounded-lg bg-error/8 border border-error/20 text-sm text-error flex items-start gap-2">
              <span className="mt-0.5 shrink-0">⚠</span>
              <span>{serverError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Email field */}
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-primary-text mb-1.5 uppercase tracking-wide">
                Email address
              </label>
              <div className="relative">
                <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text pointer-events-none" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@company.com"
                  value={form.email}
                  onChange={handleChange}
                  autoComplete="email"
                  disabled={loading}
                  className={`form-input pl-9 ${errors.email ? 'border-error focus:ring-error' : ''}`}
                />
              </div>
              {errors.email && <p className="mt-1 text-xs text-error">{errors.email}</p>}
            </div>

            {/* Password field */}
            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-primary-text mb-1.5 uppercase tracking-wide">
                Password
              </label>
              <div className="relative">
                <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text pointer-events-none" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Your password"
                  value={form.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  disabled={loading}
                  className={`form-input pl-9 pr-10 ${errors.password ? 'border-error focus:ring-error' : ''}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary-text hover:text-primary-text transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-error">{errors.password}</p>}
            </div>

            <Button type="submit" loading={loading} disabled={loading} className="w-full mt-2 py-2.5">
              Sign in
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-secondary-text">
            By signing in you agree to our terms of service and privacy policy.
          </p>
        </div>
      </div>
    </div>
  )
}
