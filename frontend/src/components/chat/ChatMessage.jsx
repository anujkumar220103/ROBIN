// Renders a single chat message — user or assistant — with safe text display.
// LLM-generated text is untrusted — dangerouslySetInnerHTML is never used.
// Assistant messages include a SpeakButton for Text-to-Speech playback.

import { User, Bot } from 'lucide-react'
import ChatSources from './ChatSources.jsx'
import SpeakButton from './SpeakButton.jsx'

/**
 * @param {object}    props
 * @param {object}    props.message     { role, content, sources?, id? }
 * @param {function}  [props.onSpeak]   speak(text, id, lang) from useSpeechSynthesis
 * @param {boolean}   [props.isPlaying] True when this message is being spoken
 * @param {string}    [props.lang]      BCP-47 language for TTS
 */
export default function ChatMessage({ message, onSpeak, isPlaying = false, lang = 'en-IN' }) {
  const isUser = message.role === 'user'
  const msgId = message.id ?? message.content.slice(0, 40)

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary text-white' : 'bg-surface border border-border'
      }`}>
        {isUser ? <User size={14} /> : <Bot size={14} className="text-secondary-text" />}
      </div>

      {/* Message bubble + speak button */}
      <div className={`flex-1 min-w-0 max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div className={`rounded-xl px-4 py-3 text-sm leading-6 ${
          isUser
            ? 'bg-primary text-white rounded-tr-sm'
            : 'bg-surface border border-border text-primary-text rounded-tl-sm'
        }`}>
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Source citations for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <ChatSources sources={message.sources} />
        )}

        {/* TTS speak button — only for assistant messages */}
        {!isUser && onSpeak && (
          <SpeakButton
            messageId={msgId}
            text={message.content}
            lang={lang}
            onSpeak={onSpeak}
            isPlaying={isPlaying}
          />
        )}
      </div>
    </div>
  )
}
