// Shown when no messages exist in the conversation.

import { Link } from 'react-router-dom'
import { MessageSquare, FileText } from 'lucide-react'

export default function ChatEmptyState({ hasDocuments }) {
  if (!hasDocuments) {
    return (
      <div className="flex flex-col items-center justify-center flex-1 text-center px-6 py-16">
        <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-4">
          <FileText size={22} className="text-secondary-text" />
        </div>
        <p className="font-medium text-primary-text mb-1">No documents available</p>
        <p className="text-sm text-secondary-text mb-4">
          Upload and process a document before testing your knowledge assistant.
        </p>
        <Link to="/dashboard/documents" className="btn-primary text-sm">
          Go to Documents
        </Link>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center flex-1 text-center px-6 py-16">
      <div className="w-12 h-12 rounded-full bg-surface border border-border flex items-center justify-center mb-4">
        <MessageSquare size={22} className="text-secondary-text" />
      </div>
      <p className="font-medium text-primary-text mb-1">Ask a question about your documents</p>
      <p className="text-sm text-secondary-text">
        Type a question below. Answers are based only on your uploaded documents.
      </p>
    </div>
  )
}
