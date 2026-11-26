// Company registration page — calls the real registration API.

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bot, Building2, User, Mail, Lock, Eye, EyeOff, CheckCircle, ArrowRight } from 'lucide-react'
import Button from '../components/common/Button.jsx'
import { authService } from '../services/authService.js'

function getErrorMessage(err) {
  if (err.response?.data?.detail) return err.response.data.detail
  if (err.message === 'Network Error') return 'Unable to reach the server. Please check your connection.'
  return 'Registration failed. Please try again.'
}

function FieldInput({ id, name, type = 'text', label, placeholder, value, onChange, error, autoComplete, disabled, icon: Icon, rightElement }) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-primary-text mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      <div className="relative">
        {Icon && (
          <Icon size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text pointer-events-none" />
        )}
        <input
          id={id}
          name={name}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          disabled={disabled}
          className={`form-input ${Icon ? 'pl-9' : ''} ${rightElement ? 'pr-10' : ''} ${error ? 'border-error focus:ring-error' : ''}`}
        />
        {rightElement && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {rightElement}
          </div>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-error">{error}</p>}
    </div>
  )
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
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
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
      setForm((prev) => ({ ...prev, password: '', confirm_password: '' }))
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-surface border border-border rounded-2xl p-10 text-center max-w-sm w-full shadow-sm">
          <div className="w-14 h-14 rounded-full bg-success/10 flex items-center justify-center mx-auto mb-5">
            <CheckCircle size={28} className="text-success" />
          </div>
          <h2 className="text-xl font-bold text-primary-text mb-2">Account created!</h2>
          <p className="text-sm text-secondary-text">Redirecting you to the login page…</p>
        </div>
      </div>
    )
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
            Start<br />for free
          </h2>
          <p className="text-white/70 text-sm leading-relaxed">
            Create your company workspace and deploy an AI knowledge assistant from your own documents — no technical setup required.
          </p>
        </div>

        {/* Steps preview */}
        <div className="relative z-10 space-y-4">
          {[
            { step: '1', label: 'Register your company' },
            { step: '2', label: 'Upload your documents' },
            { step: '3', label: 'Go live in minutes' },
          ].map(({ step, label }) => (
            <div key={step} className="flex items-center gap-3">
              <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center shrink-0">
                <span className="text-white text-xs font-bold">{step}</span>
              </div>
              <span className="text-white/80 text-xs">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-background overflow-y-auto">
        <div className="w-full max-w-sm py-6">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-bold text-primary-text">ROBIN AI</span>
              <span className="text-[9px] text-secondary-text font-medium">Retrieval-Oriented Bot for Intelligent Navigation</span>
            </div>
          </div>

          <div className="mb-7">
            <h1 className="text-2xl font-bold text-primary-text mb-1.5">Create your account</h1>
            <p className="text-sm text-secondary-text">
              Already have an account?{' '}
              <Link to="/login" className="text-accent font-semibold hover:underline">Sign in</Link>
            </p>
          </div>

          {serverError && (
            <div role="alert" className="mb-5 px-4 py-3 rounded-lg bg-error/8 border border-error/20 text-sm text-error flex items-start gap-2">
              <span className="mt-0.5 shrink-0">⚠</span>
              <span>{serverError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-4">
            <FieldInput
              id="company_name"
              name="company_name"
              label="Company name"
              placeholder="Acme Technologies"
              value={form.company_name}
              onChange={handleChange}
              error={errors.company_name}
              autoComplete="organization"
              disabled={loading}
              icon={Building2}
            />
            <FieldInput
              id="full_name"
              name="full_name"
              label="Your name"
              placeholder="Priya Sharma"
              value={form.full_name}
              onChange={handleChange}
              error={errors.full_name}
              autoComplete="name"
              disabled={loading}
              icon={User}
            />
            <FieldInput
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
              icon={Mail}
            />
            <FieldInput
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              label="Password"
              placeholder="At least 12 characters"
              value={form.password}
              onChange={handleChange}
              error={errors.password}
              autoComplete="new-password"
              disabled={loading}
              icon={Lock}
              rightElement={
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="text-secondary-text hover:text-primary-text transition-colors"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              }
            />
            <FieldInput
              id="confirm_password"
              name="confirm_password"
              type={showConfirm ? 'text' : 'password'}
              label="Confirm password"
              placeholder="Repeat your password"
              value={form.confirm_password}
              onChange={handleChange}
              error={errors.confirm_password}
              autoComplete="new-password"
              disabled={loading}
              icon={Lock}
              rightElement={
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="text-secondary-text hover:text-primary-text transition-colors"
                  tabIndex={-1}
                  aria-label={showConfirm ? 'Hide password' : 'Show password'}
                >
                  {showConfirm ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              }
            />

            <Button type="submit" loading={loading} disabled={loading} className="w-full mt-2 py-2.5">
              Create account
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-secondary-text leading-relaxed">
            By creating an account you agree to our terms of service and privacy policy.
          </p>
        </div>
      </div>
    </div>
  )
}
