// Company registration page — calls the real registration API.

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bot, CheckCircle } from 'lucide-react'
import Input from '../components/common/Input.jsx'
import Button from '../components/common/Button.jsx'
import { authService } from '../services/authService.js'

function getErrorMessage(err) {
  if (err.response?.data?.detail) return err.response.data.detail
  if (err.message === 'Network Error') return 'Unable to reach the server. Please check your connection.'
  return 'Registration failed. Please try again.'
}

export default function RegisterPage() {
  const navigate = useNavigate()

  const [form, setForm] = useState({
    company_name: '',
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')
  const [success, setSuccess] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    // Clear field-level error on change
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
    if (serverError) setServerError('')
  }

  function validate() {
    const e = {}
    if (!form.company_name.trim()) e.company_name = 'Company name is required.'
    else if (form.company_name.length > 150) e.company_name = 'Must be 150 characters or fewer.'

    if (!form.full_name.trim()) e.full_name = 'Your name is required.'
    else if (form.full_name.length > 100) e.full_name = 'Must be 100 characters or fewer.'

    if (!form.email.trim()) e.email = 'Work email is required.'
    else if (!/^\S+@\S+\.\S+$/.test(form.email)) e.email = 'Enter a valid email address.'

    if (!form.password) e.password = 'Password is required.'
    else if (form.password.length < 12) e.password = 'Password must be at least 12 characters.'
    else if (form.password.length > 128) e.password = 'Password must be 128 characters or fewer.'

    if (!form.confirm_password) e.confirm_password = 'Please confirm your password.'
    else if (form.password !== form.confirm_password) e.confirm_password = 'Passwords do not match.'

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
      // confirm_password is frontend-only validation — not sent to backend.
      await authService.register({
        company_name: form.company_name,
        full_name: form.full_name,
        email: form.email,
        password: form.password,
      })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2500)
    } catch (err) {
      setServerError(getErrorMessage(err))
      // Preserve non-sensitive form values — email and names stay, password clears.
      setForm((prev) => ({ ...prev, password: '', confirm_password: '' }))
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-surface border border-border rounded-xl p-8 text-center max-w-sm w-full">
          <div className="w-12 h-12 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={24} className="text-success" />
          </div>
          <h2 className="text-lg font-semibold text-primary-text mb-2">Account created!</h2>
          <p className="text-sm text-secondary-text">Redirecting you to the login page…</p>
        </div>
      </div>
    )
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
        <h2 className="text-white text-2xl font-bold mb-3">Start for free</h2>
        <p className="text-white/70 text-sm leading-relaxed">
          Create your company account and begin building an intelligent knowledge assistant
          from your business documents.
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

          <h1 className="text-xl font-bold text-primary-text mb-1">Create your account</h1>
          <p className="text-sm text-secondary-text mb-6">
            Already have an account?{' '}
            <Link to="/login" className="text-accent font-medium hover:underline">Sign in</Link>
          </p>

          {serverError && (
            <div role="alert" className="mb-4 px-4 py-3 rounded-lg bg-error/10 border border-error/20 text-sm text-error">
              {serverError}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <Input
              id="company_name"
              name="company_name"
              label="Company name"
              placeholder="Acme Technologies"
              value={form.company_name}
              onChange={handleChange}
              error={errors.company_name}
              autoComplete="organization"
              disabled={loading}
            />
            <Input
              id="full_name"
              name="full_name"
              label="Your name"
              placeholder="Priya Sharma"
              value={form.full_name}
              onChange={handleChange}
              error={errors.full_name}
              autoComplete="name"
              disabled={loading}
            />
            <Input
              id="email"
              name="email"
              type="email"
              label="Work email"
              placeholder="priya@acme.com"
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
              placeholder="At least 12 characters"
              value={form.password}
              onChange={handleChange}
              error={errors.password}
              autoComplete="new-password"
              disabled={loading}
            />
            <Input
              id="confirm_password"
              name="confirm_password"
              type="password"
              label="Confirm password"
              placeholder="Repeat your password"
              value={form.confirm_password}
              onChange={handleChange}
              error={errors.confirm_password}
              autoComplete="new-password"
              disabled={loading}
            />

            <Button type="submit" loading={loading} disabled={loading} className="w-full mt-2">
              Create account
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
