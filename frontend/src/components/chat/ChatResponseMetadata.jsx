// Displays technical response metadata — provider, model, latency, chunks.
// Secondary UI element — collapsed by default so the answer stays prominent.

import { useState } from 'react'
import { ChevronDown, ChevronUp, Cpu } from 'lucide-react'

export default function ChatResponseMetadata({ metadata }) {
  const [open, setOpen] = useState(false)

  if (!metadata || !metadata.provider) return null

  return (
    <div className="border-t border-border px-4 py-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-xs text-secondary-text hover:text-primary-text transition-colors"
      >
        <Cpu size={11} />
        <span>Technical details</span>
        {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
      </button>

      {open && (
        <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-secondary-text">
          <span>Provider</span>
          <span className="text-primary-text capitalize">{metadata.provider}</span>

          {metadata.model && (
            <>
              <span>Model</span>
              <span className="text-primary-text truncate">{metadata.model}</span>
            </>
          )}

          {metadata.fallback_used && (
            <>
              <span>Fallback used</span>
              <span className="text-amber-600">Yes</span>
            </>
          )}

          <span>Retrieved passages</span>
          <span className="text-primary-text">{metadata.retrieved_chunks}</span>

          <span>Context passages</span>
          <span className="text-primary-text">{metadata.context_chunks}</span>

          {metadata.latency_ms > 0 && (
            <>
              <span>Response time</span>
              <span className="text-primary-text">{(metadata.latency_ms / 1000).toFixed(1)}s</span>
            </>
          )}
        </div>
      )}
    </div>
  )
}
