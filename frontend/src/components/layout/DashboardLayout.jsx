// Dashboard layout — combines sidebar and header with a responsive main area.

import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Header from './Header.jsx'

const pageTitles = {
  '/dashboard': 'Overview',
  '/dashboard/documents': 'Documents',
  '/dashboard/playground': 'Playground',
  '/dashboard/chatbot-settings': 'Chatbot Settings',
  '/dashboard/integration': 'Integration',
  '/dashboard/profile': 'Profile',
}

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  const title = pageTitles[location.pathname] || 'Dashboard'

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header title={title} onMenuOpen={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
