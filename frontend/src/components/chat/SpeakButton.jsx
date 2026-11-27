// SpeakButton — plays or stops TTS for a single assistant message.
// Renders nothing when the Web Speech Synthesis API is not supported.

import { Volume2, VolumeX } from 'lucide-react'
import { isSpeechSynthesisSupported } from '../../hooks/useSpeechSynthesis.js'

/**
 * @param {object}   props
 * @param {string}   props.messageId     Unique key for this message
 * @param {string}   props.text          The text to speak
 * @param {string}   [props.lang]        BCP-47 language tag
 * @param {function} props.onSpeak       speak(text, id, lang) callback from useSpeechSynthesis
 * @param {boolean}  props.isPlaying     True when this message is currently being spoken
 * @param {boolean}  [props.compact]     Smaller variant for widget
 */
export default function SpeakButton({ messageId, text, lang = 'en-IN', onSpeak, isPlaying, compact = false }) {
  if (!isSpeechSynthesisSupported) return null

  const size = compact ? 12 : 13

  return (
    <button
      type="button"
      onClick={() => onSpeak(text, messageId, lang)}
      title={isPlaying ? 'Stop reading' : 'Read aloud'}
      aria-label={isPlaying ? 'Stop reading aloud' : 'Read aloud'}
      aria-pressed={isPlaying}
      className={[
        'flex items-center gap-1 rounded px-1.5 py-0.5 text-xs transition-colors',
        isPlaying
          ? 'bg-blue-50 text-blue-600 hover:bg-blue-100'
          : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100',
      ].join(' ')}
    >
      {isPlaying ? <VolumeX size={size} /> : <Volume2 size={size} />}
      <span className="sr-only">{isPlaying ? 'Stop' : 'Speak'}</span>
    </button>
  )
}
