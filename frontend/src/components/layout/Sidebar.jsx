// Dashboard sidebar — navigation, branding, company name, and logout.

import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  Settings,
  Code2,
  User,
  LogOut,
  X,
  Bot,
} from 'lucide-react'
import { useAuth } from '../../hooks/useAuth.js'

const navItems = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/dashboard/documents', label: 'Documents', icon: FileText },
  { to: '/dashboard/playground', label: 'Playground', icon: MessageSquare },
  { to: '/dashboard/chatbot-settings', label: 'Chatbot Settings', icon: Settings },
  { to: '/dashboard/integration', label: 'Integration', icon: Code2 },
  { to: '/dashboard/profile', label: 'Profile', icon: User },
]

export default function Sidebar({ open, onClose }) {
  const { company, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-0 left-0 z-30 h-full w-60 bg-surface border-r border-border
          flex flex-col transition-transform duration-200
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:z-auto
        `}
        aria-label="Sidebar navigation"
      >
        {/* Logo and mobile close */}
        <div className="flex items-center justify-between h-14 px-4 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center shrink-0">
              <Bot size={16} className="text-white" />
            </div>
            <div className="flex flex-col leading-tight min-w-0">
              <span className="text-sm font-bold text-primary-text tracking-tight">ROBIN AI</span>
              <span className="text-[8px] text-secondary-text font-medium leading-tight truncate">Retrieval-Oriented Bot for Intelligent Navigation</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded hover:bg-gray-100 text-secondary-text"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        {/* Company name */}
        {company && (
          <div className="px-4 py-3 border-b border-border">
            <p className="text-xs text-secondary-text uppercase tracking-wider font-medium">Company</p>
            <p className="text-sm font-semibold text-primary-text truncate mt-0.5">{company.name}</p>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2">
          <ul className="space-y-0.5">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'bg-accent/10 text-accent font-medium'
                        : 'text-secondary-text hover:bg-gray-50 hover:text-primary-text'
                    }`
                  }
                >
                  <Icon size={16} />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* Logout */}
        <div className="p-3 border-t border-border shrink-0">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-secondary-text hover:bg-gray-50 hover:text-error transition-colors"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>
    </>
  )
}
