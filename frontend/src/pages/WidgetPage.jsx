// Displays the isolated visitor chatbot conversation inside a same-origin iframe.
// This component intentionally does NOT use AuthContext — it is a fully public
// page served in a cross-origin iframe and must never trigger /auth/me.
//
// Voice features use the browser-native Web Speech API.
// STT: microphone button beside the input field.
// TTS: speaker button under each assistant message + auto-speak toggle.

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Send, Volume2 } from 'lucide-react'
import { createPublicSession, getPublicConfig, askPublicChatbot } from '../services/publicChatService.js'
import MicButton from '../components/chat/MicButton.jsx'
import SpeakButton from '../components/chat/SpeakButton.jsx'
import useSpeechRecognition from '../hooks/useSpeechRecognition.js'
import useSpeechSynthesis from '../hooks/useSpeechSynthesis.js'

export default function WidgetPage() {
  const { publicId } = useParams()
  const [config, setConfig] = useState(null)
  const [token, setToken] = useState('')
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [autoSpeak, setAutoSpeak] = useState(false)
  const [lang, setLang] = useState('en-IN')
  const bottomRef = useRef(null)

  // Freeze the embedding origin on first render so it cannot change between
  // re-renders or async callbacks. The session JWT is bound to this exact
  // origin; using a different value on a subsequent request causes a 401.
  const embeddingOriginRef = useRef(
    new URLSearchParams(window.location.search).get('origin') || window.location.origin
  )
  const embeddingOrigin = embeddingOriginRef.current

  // ── TTS ───────────────────────────────────────────────────────────────────
  const { speakingId, speak, stop: stopSpeech, isSupported: ttsSupported } = useSpeechSynthesis()

  // ── STT ───────────────────────────────────────────────────────────────────
  const handleSTTResult = useCallback((transcript) => {
    setQuestion((prev) => {
      const trimmed = prev.trimEnd()
      return trimmed ? `${trimmed} ${transcript}` : transcript
    })
  }, [])

  const {
    listening,
    error: sttError,
    startListening,
    stopListening,
    abortListening,
  } = useSpeechRecognition({ lang, onResult: handleSTTResult })

  function handleMicToggle() {
    if (listening) {
      stopListening()
    } else {
      stopSpeech()
      startListening()
    }
  }

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      abortListening()
      stopSpeech()
    }
  }, [abortListening, stopSpeech])

  // ── Session init ──────────────────────────────────────────────────────────
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
          id: 'welcome',
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

  // ── Send question ─────────────────────────────────────────────────────────
  async function sendQuestion(event) {
    event?.preventDefault()
    const clean = question.trim()
    if (!clean || loading || !token) return

    if (listening) stopListening()
    stopSpeech()

    setLoading(true)
    setError('')

    const history = messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role, content: m.content }))

    setMessages((prev) => [...prev, { role: 'user', content: clean, id: `user-${Date.now()}` }])
    setQuestion('')

    try {
      const response = await askPublicChatbot(publicId, token, clean, history, embeddingOrigin)
      const data = response.data

      const answer = typeof data?.answer === 'string' ? data.answer : ''
      const sources = Array.isArray(data?.sources) ? data.sources : []

      if (!answer) {
        setError('The assistant returned an empty response. Please try again.')
        setMessages((prev) => prev.slice(0, -1))
        setQuestion(clean)
        return
      }

      const msgId = `assistant-${Date.now()}`
      setMessages((prev) => [...prev, { role: 'assistant', content: answer, sources, id: msgId }])

      if (autoSpeak && ttsSupported) {
        speak(answer, msgId, lang)
      }
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

  // ── Render: loading / error before config ─────────────────────────────────
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

  const accentColor = config.primary_color || '#2563EB'

  // ── Main chat UI ──────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen flex-col bg-white">
      {/* Header */}
      <header className="px-4 py-3 text-white flex-shrink-0 flex items-center justify-between" style={{ backgroundColor: accentColor }}>
        <div className="min-w-0">
          <p className="font-semibold text-sm truncate">{config.name}</p>
          {config.description ? (
            <p className="mt-0.5 text-xs opacity-90 truncate">{config.description}</p>
          ) : null}
        </div>
        {/* Auto-speak toggle in header */}
        {ttsSupported && (
          <button
            type="button"
            onClick={() => setAutoSpeak(v => !v)}
            title={autoSpeak ? 'Disable auto voice response' : 'Enable auto voice response'}
            aria-pressed={autoSpeak}
            className={[
              'ml-3 flex-shrink-0 rounded-full p-1.5 transition-colors',
              autoSpeak ? 'bg-white/30' : 'bg-white/10 hover:bg-white/20',
            ].join(' ')}
          >
            <Volume2 size={14} />
            <span className="sr-only">{autoSpeak ? 'Disable auto-speak' : 'Enable auto-speak'}</span>
          </button>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-3 min-h-0">
        {messages.map((message, index) => (
          <div key={message.id ?? index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className="flex flex-col gap-1 max-w-[85%]">
              <div
                className={`rounded-2xl px-3 py-2 text-sm ${
                  message.role === 'user' ? 'text-white' : 'bg-gray-100 text-gray-900'
                }`}
                style={message.role === 'user' ? { backgroundColor: accentColor } : undefined}
              >
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
                {Array.isArray(message.sources) && message.sources.length > 0 && (
                  <div className="mt-2 border-t border-gray-300 pt-2 text-xs space-y-0.5">
                    {message.sources.map((source) => (
                      <p key={source.source_number}>
                        {source.source_number}. {source.title}
                        {source.page_number ? ` — page ${source.page_number}` : ''}
                      </p>
                    ))}
                  </div>
                )}
              </div>

              {/* TTS speak button under assistant messages */}
              {message.role === 'assistant' && (
                <SpeakButton
                  messageId={message.id ?? index}
                  text={message.content}
                  lang={lang}
                  onSpeak={speak}
                  isPlaying={speakingId === (message.id ?? index)}
                  compact
                />
              )}
            </div>
          </div>
        ))}

        {/* Suggested questions */}
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

      {/* STT error */}
      {sttError && (
        <p className="mx-3 mb-1 rounded-md bg-red-50 px-3 py-1.5 text-xs text-red-700">{sttError}</p>
      )}

      {/* Input row */}
      <form onSubmit={sendQuestion} className="flex items-center gap-1.5 border-t px-2 py-2 flex-shrink-0">
        {/* Language selector */}
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          disabled={loading || listening}
          aria-label="Voice language"
          className="rounded border border-gray-300 bg-white px-1.5 py-1.5 text-xs text-gray-600 focus:outline-none focus:ring-1 w-14 flex-shrink-0"
        >
          <option value="en-IN">EN</option>
          <option value="hi-IN">HI</option>
        </select>

        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className={[
            'flex-1 rounded-lg border px-3 py-2 text-sm outline-none transition',
            listening
              ? 'border-red-400 ring-1 ring-red-400'
              : 'border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500',
          ].join(' ')}
          placeholder={listening ? 'Listening… speak now' : (config.placeholder || 'Type your question…')}
          disabled={loading}
          maxLength={1000}
        />

        <MicButton
          listening={listening}
          onToggle={handleMicToggle}
          disabled={loading}
          compact
        />

        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="flex items-center justify-center rounded-lg px-2.5 py-2 text-white transition disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          style={{ backgroundColor: accentColor }}
        >
          <Send size={15} />
        </button>
      </form>

      {/* Privacy notice */}
      <p className="px-3 pb-2 text-center text-gray-400" style={{ fontSize: '10px', lineHeight: '1.4' }}>
        Voice input is processed by your browser's speech engine. No audio is stored by ROBIN AI.
      </p>
    </div>
  )
}
