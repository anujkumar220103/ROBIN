// MicButton — microphone toggle for Speech-to-Text.
// Shows a pulsing ring animation while the browser is actively listening.
// Renders nothing (null) when the Web Speech API is not supported.

import { Mic, MicOff } from 'lucide-react'
import { isSpeechRecognitionSupported } from '../../hooks/useSpeechRecognition.js'

/**
 * @param {object}   props
 * @param {boolean}  props.listening   Whether recognition is active
 * @param {function} props.onToggle    Called on click to start or stop
 * @param {boolean}  [props.disabled]  Disables the button (e.g. while loading)
 * @param {string}   [props.className] Additional Tailwind classes
 * @param {boolean}  [props.compact]   Smaller variant for the widget
 */
export default function MicButton({ listening, onToggle, disabled = false, className = '', compact = false }) {
  if (!isSpeechRecognitionSupported) return null

  const size = compact ? 14 : 16
  const pad  = compact ? 'p-1.5' : 'p-2'

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      title={listening ? 'Stop listening' : 'Start voice input (English / हिन्दी)'}
      aria-label={listening ? 'Stop listening' : 'Start voice input'}
      aria-pressed={listening}
      className={[
        'relative flex-shrink-0 rounded-lg transition-all duration-150',
        pad,
        listening
          ? 'bg-red-50 text-red-600 hover:bg-red-100'
          : 'text-secondary-text hover:bg-gray-100 hover:text-primary-text',
        disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
        className,
      ].join(' ')}
    >
      {/* Pulsing ring — visible only while listening */}
      {listening && (
        <span
          aria-hidden="true"
          className="absolute inset-0 rounded-lg animate-ping bg-red-400 opacity-25"
        />
      )}
      {listening ? <MicOff size={size} /> : <Mic size={size} />}
    </button>
  )
}
