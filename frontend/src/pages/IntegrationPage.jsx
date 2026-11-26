// Generates the website embed snippet and chatbot activation controls.

import { useEffect, useState } from 'react'
import { Check, Copy, Code2, Globe } from 'lucide-react'
import { chatbotService } from '../services/chatbotService.js'

export default function IntegrationPage() {
  const [chatbot, setChatbot] = useState(null)
  const [embed, setEmbed] = useState(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function load() {
    try {
      const [chatResponse, embedResponse] = await Promise.all([
        chatbotService.getChatbot(),
        chatbotService.getEmbedCode(),
      ])
      setChatbot(chatResponse.data)
      setEmbed(embedResponse.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Integration details could not be loaded.')
    }
  }

  useEffect(() => { load() }, [])

  async function activate() {
    if (!window.confirm('Activate this chatbot for public website visitors? Published document information may be processed by configured external AI providers.')) return
    try {
      await chatbotService.activateChatbot({
        acknowledge_public_documents: true,
        acknowledge_external_processing: true,
      })
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Chatbot could not be activated.')
    }
  }

  async function deactivate() {
    try {
      await chatbotService.deactivateChatbot()
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Chatbot could not be deactivated.')
    }
  }

  async function copyCode() {
    await navigator.clipboard.writeText(embed.embed_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-primary-text">Website Integration</h2>
        <p className="mt-1 text-sm text-secondary-text">Embed ROBIN AI on approved external websites.</p>
      </div>
      {error && <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>}
      {chatbot && embed && (
        <>
          <div className="mb-5 flex items-center justify-between rounded-xl border border-border bg-surface p-5">
            <div>
              <p className="text-sm font-semibold text-primary-text">Public status</p>
              <p className="mt-1 text-xs text-secondary-text">{chatbot.is_active ? 'This chatbot can receive public questions.' : 'This chatbot is inactive.'}</p>
            </div>
            <button className={chatbot.is_active ? 'btn-secondary' : 'btn-primary'} onClick={chatbot.is_active ? deactivate : activate}>
              {chatbot.is_active ? 'Deactivate' : 'Activate'}
            </button>
          </div>

          <div className="mb-5 rounded-xl border border-border bg-surface p-5">
            <div className="mb-3 flex items-center gap-2"><Globe size={16} /><h3 className="text-sm font-semibold">Allowed websites</h3></div>
            {chatbot.allowed_domains.length ? (
              <div className="space-y-2">{chatbot.allowed_domains.map((origin) => <p key={origin} className="flex items-center gap-2 rounded-md bg-background px-3 py-2 text-xs"><Check size={13} className="text-green-600" />{origin}</p>)}</div>
            ) : <p className="text-xs text-secondary-text">Add at least one HTTPS origin in Chatbot Settings.</p>}
          </div>

          <div className="rounded-xl border border-border bg-surface p-5">
            <div className="mb-3 flex items-center gap-2"><Code2 size={16} /><h3 className="text-sm font-semibold">Embed code</h3></div>
            <pre className="overflow-x-auto rounded-lg border border-border bg-background p-4 text-xs text-primary-text">{embed.embed_code}</pre>
            <button className="btn-primary mt-3 text-xs" onClick={copyCode}><Copy size={14} /> {copied ? 'Copied' : 'Copy embed code'}</button>
          </div>
        </>
      )}
    </div>
  )
}
