// Displays the isolated visitor chatbot conversation inside a same-origin iframe.
// This component intentionally does NOT use AuthContext — it is a fully public
// page served in a cross-origin iframe and must never trigger /auth/me.

import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Send } from 'lucide-react'
import { createPublicSession, getPublicConfig, askPublicChatbot } from '../services/publicChatService.js'

export default function WidgetPage() {
  const { publicId } = useParams()
  const [config, setConfig] = useState(null)
  const [token, setToken] = useState('')
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)

  // Freeze the embedding origin on first render so it cannot change between
  // re-renders or async callbacks. The session JWT is bound to this exact
  // origin; using a different value on a subsequent request would cause the
  // backend to reject it with 401.
  const embeddingOriginRef = useRef(
    new URLSearchParams(window.location.search).get('origin') || window.location.origin
  )
  const embeddingOrigin = embeddingOriginRef.current

  useEffect(() => {
    if (!publicId) return
    let active = true

    Promise.all([
      getPublicConfig(publicId, embeddingOrigin),
      createPublicSession(publicId, embeddingOrigin),
    ])
      .then(([configResponse, sessionResponse]) => {
        if (!active) return
        const chatbotConfig = configResponse.data
        const sessionToken = sessionResponse.data?.session_token
        if (!sessionToken) {
          setError('Could not create a chat session. Please reload the page.')
          return
        }
        setConfig(chatbotConfig)
        setToken(sessionToken)
        setMessages([{
          role: 'assistant',
          content: chatbotConfig.welcome_message || 'Hello! How can I help you today?',
        }])
      })
      .catch((err) => {
        if (!active) return
        const detail = err.response?.data?.detail
        if (err.response?.status === 403) {
          setError(detail || 'This website is not authorised to use this chatbot.')
        } else if (err.response?.status === 404) {
          setError(detail || 'This chatbot is unavailable.')
        } else if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
          setError('The chatbot took too long to respond. Please reload the page.')
        } else {
          setError(detail || 'Chatbot is unavailable. Please reload the page.')
        }
      })

    return () => { active = false }
  }, [publicId, embeddingOrigin])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendQuestion(event) {
    event?.preventDefault()
    const clean = question.trim()
    if (!clean || loading || !token) return

    setLoading(true)
    setError('')

    // Capture history before adding the new user message so the outgoing
    // request reflects the conversation state at the time of submission.
    const history = messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role, content: m.content }))

    setMessages((prev) => [...prev, { role: 'user', content: clean }])
    setQuestion('')

    try {
      const response = await askPublicChatbot(publicId, token, clean, history, embeddingOrigin)
      const data = response.data

      // Guard against unexpected response shapes before touching React state.
      const answer = typeof data?.answer === 'string' ? data.answer : ''
      const sources = Array.isArray(data?.sources) ? data.sources : []

      if (!answer) {
        setError('The assistant returned an empty response. Please try again.')
        // Remove the optimistically-added user message so the input isn't lost.
        setMessages((prev) => prev.slice(0, -1))
        setQuestion(clean)
        return
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: answer, sources }])
    } catch (err) {
      const status = err.response?.status
      const detail = err.response?.data?.detail

      if (status === 401) {
        setError('Your chat session has expired. Please reload the page to start a new one.')
      } else if (status === 403) {
        setError(detail || 'This website is not authorised to use this chatbot.')
      } else if (status === 429) {
        setError('Too many requests. Please wait a moment before asking again.')
      } else if (status === 422) {
        setError(detail || 'Your question could not be processed. Please rephrase and try again.')
      } else if (status === 503) {
        setError('The AI service is temporarily unavailable. Please try again shortly.')
      } else if (err.code === 'ECONNABORTED' || err.message?.toLowerCase().includes('timeout')) {
        setError('The request timed out. Please try a shorter question or try again.')
      } else {
        setError(detail || 'The answer could not be generated. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  // ── Loading / error state before config is available ──────────────────────
  if (!config) {
    return (
      <div className="flex h-screen items-center justify-center p-6 text-sm text-gray-500">
        {error ? (
          <p className="rounded-md bg-red-50 px-4 py-3 text-xs text-red-700 max-w-xs text-center">
            {error}
          </p>
        ) : (
          'Loading chatbot…'
        )}
      </div>
    )
  }

  // ── Main chat UI ───────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="px-4 py-3 text-white flex-shrink-0" style={{ backgroundColor: config.primary_color || '#2563EB' }}>
        <p className="font-semibold text-sm">{config.name}</p>
        {config.description ? (
          <p className="mt-0.5 text-xs opacity-90">{config.description}</p>
        ) : null}
      </header>

      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-3 min-h-0">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                message.role === 'user' ? 'text-white' : 'bg-gray-100 text-gray-900'
              }`}
              style={message.role === 'user' ? { backgroundColor: config.primary_color || '#2563EB' } : undefined}
            >
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
              {Array.isArray(message.sources) && message.sources.length > 0 && (
                <div className="mt-2 border-t border-white/30 pt-2 text-xs opacity-90 space-y-0.5">
                  {message.sources.map((source) => (
                    <p key={source.source_number}>
                      {source.source_number}. {source.title}
                      {source.page_number ? ` — page ${source.page_number}` : ''}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Suggested questions — only shown when the welcome message is the only message */}
        {Array.isArray(config.suggested_questions) &&
          config.suggested_questions.length > 0 &&
          messages.length === 1 && (
            <div className="flex flex-wrap gap-2">
              {config.suggested_questions.map((item) => (
                <button
                  key={item}
                  onClick={() => setQuestion(item)}
                  className="rounded-full border border-gray-300 bg-white px-3 py-1 text-xs text-gray-700 hover:bg-gray-50 transition"
                >
                  {item}
                </button>
              ))}
            </div>
          )}

        {loading && (
          <div className="flex justify-start">
            <p className="text-xs text-gray-400 italic px-1">Thinking…</p>
          </div>
        )}

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={sendQuestion} className="flex gap-2 border-t p-3 flex-shrink-0">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          placeholder={config.placeholder || 'Type your question…'}
          disabled={loading}
          maxLength={1000}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="flex items-center justify-center rounded-lg px-3 py-2 text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ backgroundColor: config.primary_color || '#2563EB' }}
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  )
}
