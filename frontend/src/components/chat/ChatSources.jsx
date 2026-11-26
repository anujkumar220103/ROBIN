// Displays validated source citations below an assistant answer.
// Only backend-validated sources are shown — fabricated citations are never displayed.

import { useState } from 'react'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'

export default function ChatSources({ sources }) {
  const [expanded, setExpanded] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="w-full">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-secondary-text hover:text-primary-text transition-colors"
      >
        <FileText size={12} />
        <span>{sources.length} source{sources.length > 1 ? 's' : ''}</span>
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {expanded && (
        <div className="mt-2 space-y-2">
          {sources.map((src, index) => (
            <div
              key={src.chunk_id || index}
              className="rounded-lg border border-border bg-background px-3 py-2.5 text-xs"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span className="font-medium text-primary text-xs bg-primary/10 px-1.5 py-0.5 rounded">
                  [{src.source_id}]
                </span>
                <FileText size={11} className="text-secondary-text" />
                <span className="font-medium text-primary-text truncate">{src.filename}</span>
                <span className="text-secondary-text ml-auto flex-shrink-0">Page {src.page_number}</span>
              </div>
              {src.excerpt && (
                <p className="text-secondary-text leading-5 line-clamp-3">{src.excerpt}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
