// Profile page — view and update user name and company name using real APIs.

import { useState } from 'react'
import { CheckCircle } from 'lucide-react'
import Input from '../components/common/Input.jsx'
import Button from '../components/common/Button.jsx'
import { useAuth } from '../hooks/useAuth.js'
import { authService } from '../services/authService.js'
import { companyService } from '../services/companyService.js'

function getError(err) {
  if (err.response?.data?.detail) return err.response.data.detail
  return 'Update failed. Please try again.'
}

export default function ProfilePage() {
  const { user, company, updateUserProfile, updateCompanyProfile } = useAuth()

  // --- User profile ---
  const [userName, setUserName] = useState(user?.full_name || '')
  const [userLoading, setUserLoading] = useState(false)
  const [userError, setUserError] = useState('')
  const [userSuccess, setUserSuccess] = useState(false)

  // --- Company profile ---
  const [companyName, setCompanyName] = useState(company?.name || '')
  const [companyLoading, setCompanyLoading] = useState(false)
  const [companyError, setCompanyError] = useState('')
  const [companySuccess, setCompanySuccess] = useState(false)

  async function handleUserSave(e) {
    e.preventDefault()
    setUserError('')
    setUserSuccess(false)
    if (!userName.trim()) { setUserError('Name cannot be empty.'); return }
    if (userName.length > 100) { setUserError('Name must be 100 characters or fewer.'); return }

    setUserLoading(true)
    try {
      const data = await authService.updateProfile({ full_name: userName.trim() })
      updateUserProfile(data.user)
      setUserSuccess(true)
      setTimeout(() => setUserSuccess(false), 3000)
    } catch (err) {
      setUserError(getError(err))
    } finally {
      setUserLoading(false)
    }
  }

  async function handleCompanySave(e) {
    e.preventDefault()
    setCompanyError('')
    setCompanySuccess(false)
    if (!companyName.trim()) { setCompanyError('Company name cannot be empty.'); return }
    if (companyName.length > 150) { setCompanyError('Must be 150 characters or fewer.'); return }

    setCompanyLoading(true)
    try {
      const data = await companyService.updateCompany({ name: companyName.trim() })
      updateCompanyProfile(data)
      setCompanySuccess(true)
      setTimeout(() => setCompanySuccess(false), 3000)
    } catch (err) {
      setCompanyError(getError(err))
    } finally {
      setCompanyLoading(false)
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Personal information */}
      <section className="bg-surface border border-border rounded-xl">
        <div className="px-5 py-4 border-b border-border">
          <h3 className="text-sm font-semibold text-primary-text">Personal Information</h3>
        </div>
        <form onSubmit={handleUserSave} className="p-5 space-y-4">
          <Input
            id="full_name"
            label="Full name"
            value={userName}
            onChange={(e) => { setUserName(e.target.value); setUserError('') }}
            error={userError}
            disabled={userLoading}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-primary-text mb-1">Email</label>
              <input
                disabled
                value={user?.email || ''}
                className="form-input text-secondary-text"
                aria-label="Email address (read-only)"
              />
              <p className="text-xs text-secondary-text mt-1">Email cannot be changed.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-primary-text mb-1">Role</label>
              <input
                disabled
                value={user?.role?.replace('_', ' ') || ''}
                className="form-input text-secondary-text capitalize"
                aria-label="Role (read-only)"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button type="submit" loading={userLoading} disabled={userLoading}>
              Save changes
            </Button>
            {userSuccess && (
              <span className="flex items-center gap-1.5 text-sm text-success">
                <CheckCircle size={14} /> Saved
              </span>
            )}
          </div>
        </form>
      </section>

      {/* Company information */}
      <section className="bg-surface border border-border rounded-xl">
        <div className="px-5 py-4 border-b border-border">
          <h3 className="text-sm font-semibold text-primary-text">Company Information</h3>
        </div>
        <form onSubmit={handleCompanySave} className="p-5 space-y-4">
          <Input
            id="company_name"
            label="Company name"
            value={companyName}
            onChange={(e) => { setCompanyName(e.target.value); setCompanyError('') }}
            error={companyError}
            disabled={companyLoading}
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-primary-text mb-1">Company ID</label>
              <input
                disabled
                value={company?.slug || ''}
                className="form-input text-secondary-text font-mono text-xs"
                aria-label="Company slug (read-only)"
              />
              <p className="text-xs text-secondary-text mt-1">Slug — used in internal identifiers.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-primary-text mb-1">Member since</label>
              <input
                disabled
                value={company?.created_at ? new Date(company.created_at).toLocaleDateString() : '—'}
                className="form-input text-secondary-text"
                aria-label="Account creation date (read-only)"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button type="submit" loading={companyLoading} disabled={companyLoading}>
              Update company name
            </Button>
            {companySuccess && (
              <span className="flex items-center gap-1.5 text-sm text-success">
                <CheckCircle size={14} /> Saved
              </span>
            )}
          </div>
        </form>
      </section>
    </div>
  )
}
