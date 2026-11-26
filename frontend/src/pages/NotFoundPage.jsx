// 404 page — shown for routes that don't exist.

import { Link } from 'react-router-dom'
import { Bot } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="text-center">
        <div className="w-14 h-14 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
          <Bot size={28} className="text-accent" />
        </div>
        <h1 className="text-5xl font-bold text-primary-text mb-2">404</h1>
        <p className="text-secondary-text text-sm mb-6 max-w-xs mx-auto">
          The page you're looking for doesn't exist.
        </p>
        <Link to="/" className="btn-primary px-5 py-2.5">
          Back to home
        </Link>
      </div>
    </div>
  )
}
