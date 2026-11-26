// Dashboard header — page title, mobile menu toggle, and user info.

import { Menu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth.js'

export default function Header({ title, onMenuOpen }) {
  const { user } = useAuth()

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  return (
    <header className="h-14 bg-surface border-b border-border flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobile menu button */}
        <button
          onClick={onMenuOpen}
          className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 text-secondary-text"
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>
        <h1 className="text-sm font-semibold text-primary-text">{title}</h1>
      </div>

      <Link
        to="/dashboard/profile"
        className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
        aria-label="Go to profile"
      >
        <div className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center">
          <span className="text-xs font-semibold text-accent">{initials}</span>
        </div>
        <span className="hidden sm:block text-sm text-primary-text font-medium truncate max-w-[140px]">
          {user?.full_name}
        </span>
      </Link>
    </header>
  )
}
