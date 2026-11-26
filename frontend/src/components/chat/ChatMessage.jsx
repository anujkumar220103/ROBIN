// Renders a single chat message — user or assistant — with safe text display.
// LLM-generated text untrusted hai — dangerouslySetInnerHTML avoid karte hain.

import { User, Bot } from 'lucide-react'
import ChatSources from './ChatSources.jsx'

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary text-white' : 'bg-surface border border-border'
      }`}>
        {isUser ? <User size={14} /> : <Bot size={14} className="text-secondary-text" />}
      </div>

      {/* Message bubble */}
      <div className={`flex-1 min-w-0 max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-2`}>
        <div className={`rounded-xl px-4 py-3 text-sm leading-6 ${
          isUser
            ? 'bg-primary text-white rounded-tr-sm'
            : 'bg-surface border border-border text-primary-text rounded-tl-sm'
        }`}>
          {/* Render as plain text — no dangerouslySetInnerHTML, no script execution */}
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Source citations for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <ChatSources sources={message.sources} />
        )}
      </div>
    </div>
  )
}
