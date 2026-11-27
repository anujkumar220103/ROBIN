// Message input composer — handles text entry, submission, keyboard shortcuts,
// and voice input (Speech-to-Text via the browser's native Web Speech API).

import { useRef } from 'react'
import { Send, Loader2 } from 'lucide-react'
import MicButton from './MicButton.jsx'
import { isSpeechRecognitionSupported } from '../../hooks/useSpeechRecognition.js'

const MAX_CHARS = 1000

// Language options for voice input.
const LANG_OPTIONS = [
  { value: 'en-IN', label: 'EN' },
  { value: 'hi-IN', label: 'HI' },
]

/**
 * @param {object}   props
 * @param {string}   props.value          Current textarea value
 * @param {function} props.onChange       Called with new string value
 * @param {function} props.onSubmit       Called (no args) to submit the message
 * @param {boolean}  props.loading        Disables input and shows spinner
 * @param {boolean}  props.listening      True while STT is active
 * @param {function} props.onMicToggle    Called to start/stop listening
 * @param {string}   props.lang           Current BCP-47 language for STT ('en-IN'|'hi-IN')
 * @param {function} props.onLangChange   Called with new lang string
 * @param {string}   [props.sttError]     Error message from STT to display
 */
export default function ChatComposer({
  value,
  onChange,
  onSubmit,
  loading,
  listening = false,
  onMicToggle,
  lang = 'en-IN',
  onLangChange,
  sttError,
}) {
  const textareaRef = useRef(null)

  function handleKeyDown(event) {
    // Enter sends; Shift+Enter inserts newline.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      if (!loading && value.trim()) {
        onSubmit()
      }
    }
  }

  function handleChange(event) {
    const val = event.target.value
    if (val.length <= MAX_CHARS) onChange(val)
  }

  const remaining = MAX_CHARS - value.length
  const isNearLimit = remaining < 100
  const showSTTNote = isSpeechRecognitionSupported

  return (
    <div className="border-t border-border bg-surface p-4">
      {/* STT browser privacy notice — shown once so users know audio leaves the device */}
      {showSTTNote && (
        <p className="text-xs text-secondary-text mb-2 leading-relaxed">
          <span className="font-medium">Voice input</span> is processed by your browser's speech engine
          (audio may be sent to the browser vendor's servers).{' '}
          <span>No audio is stored by ROBIN AI.</span>
        </p>
      )}

      {/* STT error banner */}
      {sttError && (
        <p className="mb-2 rounded-md bg-red-50 px-3 py-1.5 text-xs text-red-700">{sttError}</p>
      )}

      <div className="flex gap-2 items-end">
        {/* Language selector — only shown when STT is supported */}
        {isSpeechRecognitionSupported && (
          <select
            value={lang}
            onChange={(e) => onLangChange?.(e.target.value)}
            disabled={loading || listening}
            title="Voice input language"
            aria-label="Voice input language"
            className="form-input w-16 py-2 text-xs flex-shrink-0 cursor-pointer"
          >
            {LANG_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        )}

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={
              listening
                ? 'Listening… speak now'
                : 'Ask a question about your documents… (Enter to send, Shift+Enter for new line)'
            }
            rows={3}
            disabled={loading}
            className={[
              'form-input resize-none w-full pr-16 text-sm leading-6 disabled:opacity-60',
              listening ? 'border-red-400 ring-1 ring-red-400' : '',
            ].join(' ')}
          />
          {isNearLimit && (
            <span
              className={`absolute bottom-2 right-2 text-xs ${remaining < 20 ? 'text-red-500' : 'text-secondary-text'}`}
            >
              {remaining}
            </span>
          )}
        </div>

        {/* Mic button */}
        <MicButton
          listening={listening}
          onToggle={onMicToggle}
          disabled={loading}
        />

        {/* Send button */}
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
