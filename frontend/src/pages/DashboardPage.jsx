// Dashboard overview page — welcome message, company info, and actual backend health.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  FileText,
  MessageSquare,
  Settings,
  Code2,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth.js'
import { healthService } from '../services/healthService.js'
import { documentService } from '../services/documentService.js'

function HealthBadge() {
  const [health, setHealth] = useState({ status: 'loading' })

  useEffect(() => {
    healthService.getDatabaseHealth()
      .then(() => setHealth({ status: 'healthy' }))
      .catch(() => setHealth({ status: 'unhealthy' }))
  }, [])

  if (health.status === 'loading') {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-secondary-text">
        <Loader2 size={12} className="animate-spin" /> Checking…
      </span>
    )
  }

  if (health.status === 'healthy') {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-success font-medium">
        <CheckCircle size={12} /> Connected
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-error font-medium">
      <AlertCircle size={12} /> Unavailable
    </span>
  )
}

const quickLinks = [
  {
    to: '/dashboard/documents',
    icon: FileText,
    title: 'Documents',
    description: 'Upload and manage your company PDF files.',
    phase: null,
  },
  {
    to: '/dashboard/playground',
    icon: MessageSquare,
    title: 'Playground',
    description: 'Test your chatbot with questions from your knowledge base.',
    phase: null,
  },
  {
    to: '/dashboard/chatbot-settings',
    icon: Settings,
    title: 'Chatbot Settings',
    description: 'Configure your chatbot name and appearance.',
    phase: 'Future',
  },
  {
    to: '/dashboard/integration',
    icon: Code2,
    title: 'Integration',
    description: 'Embed your chatbot on any website.',
    phase: 'Future',
  },
]

export default function DashboardPage() {
  const { user, company } = useAuth()
  const [documentStats, setDocumentStats] = useState(null)

  useEffect(() => {
    documentService.getKnowledgeBaseStats()
      .then((response) => setDocumentStats(response.data))
      .catch(() => setDocumentStats(null))
  }, [])

  return (
    <div className="max-w-4xl">
      {/* Welcome */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-primary-text">
          Welcome, {user?.full_name?.split(' ')[0] || 'there'} 👋
        </h2>
        <p className="text-sm text-secondary-text mt-1">
          {company?.name} · Company Dashboard
        </p>
      </div>

      {/* Status card */}
      <div className="bg-surface border border-border rounded-xl p-5 mb-6">
        <h3 className="text-sm font-semibold text-primary-text mb-3">System Status</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-secondary-text">Database</p>
            <HealthBadge />
          </div>
          <div>
            <p className="text-xs text-secondary-text">Account</p>
            <span className="inline-flex items-center gap-1.5 text-xs text-success font-medium">
              <CheckCircle size={12} /> Active
            </span>
          </div>
          <div>
            <p className="text-xs text-secondary-text">RAG Pipeline</p>
            <span className="inline-flex items-center gap-1.5 text-xs text-secondary-text">
              Retrieval ready
            </span>
          </div>

          {documentStats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              {[
                ['Uploaded documents', documentStats.total_documents],
                ['Ready documents', documentStats.ready_documents],
                ['Indexed chunks', documentStats.total_chunks],
                ['Processing or failed', documentStats.processing_documents + documentStats.failed_documents],
              ].map(([label, value]) => (
                <div key={label} className="border border-border rounded-lg px-4 py-3">
                  <p className="text-xs text-secondary-text">{label}</p>
                  <p className="text-lg font-semibold text-primary-text mt-1">{value}</p>
                </div>
              ))}
            </div>
          )}
          <div>
            <p className="text-xs text-secondary-text">Chatbot</p>
            <span className="inline-flex items-center gap-1.5 text-xs text-secondary-text">
              Phase 6
            </span>
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div>
        <h3 className="text-sm font-semibold text-primary-text mb-3">Get Started</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {quickLinks.map(({ to, icon: Icon, title, description, phase }) => (
            <Link
              key={to}
              to={to}
              className="bg-surface border border-border rounded-xl p-5 hover:border-accent/40 hover:shadow-sm transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-lg bg-background flex items-center justify-center group-hover:bg-accent/10 transition-colors">
                  <Icon size={18} className="text-secondary-text group-hover:text-accent transition-colors" />
                </div>
                {phase && (
                  <span className="text-xs text-secondary-text bg-gray-100 px-2 py-0.5 rounded-full">{phase}</span>
                )}
              </div>
              <p className="text-sm font-semibold text-primary-text mb-1">{title}</p>
              <p className="text-xs text-secondary-text">{description}</p>
              <div className="flex items-center gap-1 mt-3 text-xs text-accent opacity-0 group-hover:opacity-100 transition-opacity">
                Go to {title} <ArrowRight size={12} />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
