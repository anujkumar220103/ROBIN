// Message input composer — handles text entry, submission, and keyboard shortcuts.

import { useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'

const MAX_CHARS = 1000

export default function ChatComposer({ value, onChange, onSubmit, loading }) {
  const textareaRef = useRef(null)

  function handleKeyDown(event) {
    // Enter sends message; Shift+Enter inserts a newline.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!loading && value.trim()) {
        onSubmit()
      }
    }
  }

  function handleChange(event) {
    const val = event.target.value
    if (val.length <= MAX_CHARS) {
      onChange(val)
    }
  }

  const remaining = MAX_CHARS - value.length
  const isNearLimit = remaining < 100

  return (
    <div className="border-t border-border bg-surface p-4">
      <div className="flex gap-3 items-end">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents… (Enter to send, Shift+Enter for new line)"
            rows={3}
            disabled={loading}
            className="form-input resize-none w-full pr-16 text-sm leading-6 disabled:opacity-60"
          />
          {isNearLimit && (
            <span className={`absolute bottom-2 right-2 text-xs ${remaining < 20 ? 'text-red-500' : 'text-secondary-text'}`}>
              {remaining}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || !value.trim()}
          className="btn-primary flex-shrink-0 h-10 px-4 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
      <p className="text-xs text-secondary-text mt-2">
        Answers are generated from your uploaded documents only. Relevant passages may be processed by a configured AI provider.
      </p>
    </div>
  )
}
