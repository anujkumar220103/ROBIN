// Displays the isolated visitor chatbot conversation inside a same-origin iframe.

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
  const embeddingOrigin = new URLSearchParams(window.location.search).get('origin') || window.location.origin
  const bottomRef = useRef(null)

  useEffect(() => {
    let active = true
    Promise.all([getPublicConfig(publicId, embeddingOrigin), createPublicSession(publicId, embeddingOrigin)])
      .then(([configResponse, sessionResponse]) => {
        if (!active) return
        setConfig(configResponse.data)
        setToken(sessionResponse.data.session_token)
        setMessages([{ role: 'assistant', content: configResponse.data.welcome_message }])
      })
      .catch((err) => setError(err.response?.data?.detail || 'Chatbot is unavailable.'))
    return () => { active = false }
  }, [publicId, embeddingOrigin])

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages, loading])

  async function sendQuestion(event) {
    event?.preventDefault()
    const clean = question.trim()
    if (!clean || loading || !token) return
    setLoading(true)
    setError('')
    const history = messages.map((message) => ({ role: message.role, content: message.content }))
    setMessages((items) => [...items, { role: 'user', content: clean }])
    setQuestion('')
    try {
      const response = await askPublicChatbot(publicId, token, clean, history, embeddingOrigin)
      setMessages((items) => [...items, {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
      }])
    } catch (err) {
      setError(err.response?.data?.detail || 'The answer could not be generated.')
    } finally {
      setLoading(false)
    }
  }

  if (!config) {
    return <div className="flex h-screen items-center justify-center p-6 text-sm text-secondary-text">{error || 'Loading chatbot…'}</div>
  }

  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="px-4 py-3 text-white" style={{ backgroundColor: config.primary_color }}>
        <p className="font-semibold">{config.name}</p>
        <p className="mt-0.5 text-xs opacity-90">{config.description}</p>
      </header>
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-3">
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${message.role === 'user' ? 'text-white' : 'bg-gray-100 text-gray-900'}`}
              style={message.role === 'user' ? { backgroundColor: config.primary_color } : undefined}>
              <p className="whitespace-pre-wrap">{message.content}</p>
              {message.sources?.length > 0 && (
                <div className="mt-2 border-t border-gray-300 pt-2 text-xs">
                  {message.sources.map((source) => <p key={source.source_number}>{source.source_number}. {source.title}{source.page_number ? ` — page ${source.page_number}` : ''}</p>)}
                </div>
              )}
            </div>
          </div>
        ))}
        {config.suggested_questions?.length > 0 && messages.length === 1 && (
          <div className="flex flex-wrap gap-2">
            {config.suggested_questions.map((item) => (
              <button key={item} onClick={() => setQuestion(item)} className="rounded-full border px-3 py-1 text-xs">{item}</button>
            ))}
          </div>
        )}
        {loading && <p className="text-xs text-secondary-text">Thinking…</p>}
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">{error}</p>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={sendQuestion} className="flex gap-2 border-t p-3">
        <input value={question} onChange={(event) => setQuestion(event.target.value)} className="form-input flex-1" placeholder={config.placeholder} />
        <button type="submit" className="btn-primary px-3" disabled={loading || !question.trim()}><Send size={16} /></button>
      </form>
    </div>
  )
}
