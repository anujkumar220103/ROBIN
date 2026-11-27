// Provides the authenticated knowledge base chatbot interface.
// Two modes: Chat (RAG answers with citations) and Retrieval (raw passage search).
// Includes Speech-to-Text (voice input) and Text-to-Speech (voice output) via
// the browser-native Web Speech API.

import { useState, useRef, useEffect, useCallback } from 'react'
import { RefreshCw, MessageSquare, Search, FileText, Loader2, AlertCircle, Volume2 } from 'lucide-react'
import { chatService } from '../services/chatService.js'
import { knowledgeBaseService } from '../services/knowledgeBaseService.js'
import { documentService } from '../services/documentService.js'
import ChatMessage from '../components/chat/ChatMessage.jsx'
import ChatComposer from '../components/chat/ChatComposer.jsx'
import ChatEmptyState from '../components/chat/ChatEmptyState.jsx'
import ChatResponseMetadata from '../components/chat/ChatResponseMetadata.jsx'
import useSpeechRecognition from '../hooks/useSpeechRecognition.js'
import useSpeechSynthesis from '../hooks/useSpeechSynthesis.js'

const MODES = { CHAT: 'chat', RETRIEVAL: 'retrieval' }

export default function PlaygroundPage() {
  const [mode, setMode] = useState(MODES.CHAT)

  // Chat state
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const [lastMetadata, setLastMetadata] = useState(null)
  const [hasDocuments, setHasDocuments] = useState(true)

  // Retrieval state
  const [searchQuery, setSearchQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [searched, setSearched] = useState(false)

  // Voice state
  const [lang, setLang] = useState('en-IN')
  const [autoSpeak, setAutoSpeak] = useState(false)

  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)

  // ── TTS ───────────────────────────────────────────────────────────────────
  const { speakingId, speak, stop: stopSpeech, isSupported: ttsSupported } = useSpeechSynthesis()

  // ── STT ───────────────────────────────────────────────────────────────────
  const handleSTTResult = useCallback((transcript) => {
    setInputValue((prev) => {
      const trimmed = prev.trimEnd()
      return trimmed ? `${trimmed} ${transcript}` : transcript
    })
  }, [])

  const handleSTTInterim = useCallback((interim) => {
    // Show interim text visually (appended without committing) so the user
    // can see the recognition in progress.  We only update if the textarea
    // is currently empty to avoid clobbering typed text.
    // (Intentionally not wiring interim into inputValue here — final result
    //  replaces it cleanly via handleSTTResult.)
    void interim
  }, [])

  const {
    listening,
    error: sttError,
    startListening,
    stopListening,
    abortListening,
    isSupported: sttSupported,
  } = useSpeechRecognition({ lang, onResult: handleSTTResult, onInterim: handleSTTInterim })

  function handleMicToggle() {
    if (listening) {
      stopListening()
    } else {
      // Stop any active TTS before starting the microphone.
      stopSpeech()
      startListening()
    }
  }

  // Check if company has ready documents.
  useEffect(() => {
    documentService.getKnowledgeBaseStats()
      .then(res => setHasDocuments((res.data.ready_documents || 0) > 0))
      .catch(() => setHasDocuments(false))
  }, [])

  // Auto-scroll to latest message.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatLoading])

  // Stop speech and listening when the page is closed / mode changes.
  useEffect(() => {
    return () => {
      abortListening()
      stopSpeech()
    }
  }, [abortListening, stopSpeech])

  function startNewConversation() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortListening()
    stopSpeech()
    setMessages([])
    setInputValue('')
    setChatError('')
    setLastMetadata(null)
  }

  async function handleSend() {
    const question = inputValue.trim()
    if (!question || chatLoading) return

    // Stop listening/speaking before sending.
    if (listening) stopListening()
    stopSpeech()

    const history = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(-6)
      .map(m => ({ role: m.role, content: m.content }))

    setMessages(prev => [...prev, { role: 'user', content: question, id: `user-${Date.now()}` }])
    setInputValue('')
    setChatLoading(true)
    setChatError('')

    abortControllerRef.current = new AbortController()

    try {
      const res = await chatService.askQuestion(question, history, abortControllerRef.current.signal)
      const data = res.data

      const msgId = `assistant-${Date.now()}`
      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        status: data.status,
        id: msgId,
      }

      setMessages(prev => [...prev, assistantMessage])
      setLastMetadata(data.metadata || null)

      // Auto-speak the new assistant answer if the toggle is on.
      if (autoSpeak && ttsSupported) {
        speak(data.answer, msgId, lang)
      }
    } catch (err) {
      if (err.name === 'CanceledError' || err.code === 'ERR_CANCELED') return

      const status = err.response?.status
      let errorMsg = 'Something went wrong. Please try again.'

      if (status === 429) {
        errorMsg = 'You have reached the request limit. Please wait a moment before asking again.'
      } else if (status === 503) {
        errorMsg = 'The AI service is temporarily unavailable. Please try again shortly.'
      } else if (status === 504) {
        errorMsg = 'The request timed out. Please try a shorter question or try again.'
      } else if (status === 422) {
        errorMsg = err.response?.data?.detail || 'Invalid question. Please check your input.'
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        errorMsg = 'The request timed out. The AI service may be under load. Please try again.'
      }

      setChatError(errorMsg)
    } finally {
      setChatLoading(false)
    }
  }

  async function handleSearch(event) {
    event.preventDefault()
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    setSearchError('')
    setSearched(true)
    try {
      const res = await knowledgeBaseService.search(searchQuery.trim(), topK)
      setSearchResults(res.data.results)
    } catch (err) {
      setSearchResults([])
      setSearchError(err.response?.data?.detail || 'Search could not be completed.')
    } finally {
      setSearchLoading(false)
    }
  }

  return (
    <div className="max-w-4xl flex flex-col h-full">
      {/* Header */}
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-primary-text">Playground</h2>
          <p className="text-sm text-secondary-text mt-0.5">
            Test how your knowledge assistant answers questions using your uploaded documents.
          </p>
        </div>
        {mode === MODES.CHAT && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Auto-speak toggle */}
            {ttsSupported && (
              <button
                type="button"
                onClick={() => setAutoSpeak(v => !v)}
                title={autoSpeak ? 'Disable auto voice response' : 'Enable auto voice response'}
                aria-pressed={autoSpeak}
                className={[
                  'flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-colors',
                  autoSpeak
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border bg-surface text-secondary-text hover:text-primary-text',
                ].join(' ')}
              >
                <Volume2 size={13} />
                Auto-speak {autoSpeak ? 'On' : 'Off'}
              </button>
            )}
            <button
              onClick={startNewConversation}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <RefreshCw size={14} />
              New conversation
            </button>
          </div>
        )}
      </div>

      {/* Mode selector */}
      <div className="flex gap-1 mb-5 bg-surface border border-border rounded-lg p-1 w-fit">
        <button
          onClick={() => setMode(MODES.CHAT)}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === MODES.CHAT
              ? 'bg-background text-primary-text shadow-sm border border-border'
              : 'text-secondary-text hover:text-primary-text'
          }`}
        >
          <MessageSquare size={14} />
          Chat
        </button>
        <button
          onClick={() => setMode(MODES.RETRIEVAL)}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === MODES.RETRIEVAL
              ? 'bg-background text-primary-text shadow-sm border border-border'
              : 'text-secondary-text hover:text-primary-text'
          }`}
        >
          <Search size={14} />
          Retrieval
        </button>
      </div>

      {/* Chat mode */}
      {mode === MODES.CHAT && (
        <div className="flex flex-col rounded-xl border border-border bg-surface overflow-hidden" style={{ minHeight: '520px' }}>
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !chatLoading ? (
              <ChatEmptyState hasDocuments={hasDocuments} />
            ) : (
              messages.map(msg => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onSpeak={msg.role === 'assistant' ? speak : undefined}
                  isPlaying={speakingId === (msg.id ?? msg.content.slice(0, 40))}
                  lang={lang}
                />
              ))
            )}

            {chatLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-surface border border-border flex-shrink-0">
                  <Loader2 size={14} className="animate-spin text-secondary-text" />
                </div>
                <div className="bg-surface border border-border rounded-xl rounded-tl-sm px-4 py-3">
                  <span className="text-xs text-secondary-text">Searching documents and generating answer…</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Error banner */}
          {chatError && (
            <div className="mx-4 mb-2 flex items-start gap-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2.5 text-sm text-red-700">
              <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />
              <span>{chatError}</span>
            </div>
          )}

          {/* Technical metadata */}
          {lastMetadata && <ChatResponseMetadata metadata={lastMetadata} />}

          {/* Input composer with STT */}
          <ChatComposer
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSend}
            loading={chatLoading}
            listening={listening}
            onMicToggle={handleMicToggle}
            lang={lang}
            onLangChange={setLang}
            sttError={sttError}
          />
        </div>
      )}

      {/* Retrieval mode */}
      {mode === MODES.RETRIEVAL && (
        <div>
          <p className="text-sm text-secondary-text mb-4">
            Retrieval mode shows raw passages from your documents without generating an AI answer.
            Use this to verify that relevant content is indexed correctly.
          </p>

          <form onSubmit={handleSearch} className="flex gap-3 mb-5">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text" />
              <input
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="form-input pl-9"
                placeholder="Search your knowledge base"
                maxLength={1000}
              />
            </div>
            <select
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
              className="form-input w-24"
            >
              {[1, 3, 5, 10, 20].map(v => (
                <option key={v} value={v}>Top {v}</option>
              ))}
            </select>
            <button
              type="submit"
              className="btn-primary"
              disabled={searchLoading || !searchQuery.trim()}
            >
              {searchLoading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              Search
            </button>
          </form>

          {searchError && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">{searchError}</div>
          )}

          {searchLoading ? (
            <div className="flex min-h-52 items-center justify-center text-sm text-secondary-text">
              <Loader2 size={18} className="animate-spin mr-2" /> Searching…
            </div>
          ) : searchResults.length > 0 ? (
            <div className="space-y-3">
              {searchResults.map(result => (
                <article key={result.chunk_id} className="rounded-xl border border-border bg-surface p-4">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <FileText size={16} className="text-secondary-text" />
                      <div>
                        <p className="text-sm font-medium text-primary-text">{result.filename}</p>
                        <p className="text-xs text-secondary-text">Page {result.page_number}</p>
                      </div>
                    </div>
                    <span className="rounded-full bg-background px-2 py-1 text-xs text-secondary-text">
                      Similarity: {result.similarity.toFixed(3)}
                    </span>
                  </div>
                  <p className="text-sm leading-6 text-primary-text whitespace-pre-wrap">{result.text}</p>
                </article>
              ))}
            </div>
          ) : searched ? (
            <div className="rounded-xl border border-border p-10 text-center">
              <p className="text-sm font-medium text-primary-text">No relevant passages found</p>
              <p className="mt-1 text-xs text-secondary-text">Upload and index documents, then try a different query.</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
