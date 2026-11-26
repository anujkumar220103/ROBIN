// Configures chatbot identity, appearance, behavior, and allowed website origins.

import { useEffect, useState } from 'react'
import { Save, Plus, Trash2 } from 'lucide-react'
import { chatbotService } from '../services/chatbotService.js'

export default function ChatbotSettingsPage() {
  const [form, setForm] = useState(null)
  const [domain, setDomain] = useState('')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  useEffect(() => {
    chatbotService.getChatbot().then((response) => setForm(response.data)).catch((err) => setError(err.response?.data?.detail || 'Settings could not be loaded.'))
  }, [])

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function addDomain() {
    if (!domain.trim()) return
    update('allowed_domains', [...(form.allowed_domains || []), domain.trim()])
    setDomain('')
  }

  async function saveSettings(event) {
    event.preventDefault()
    setError('')
    setSaved('')
    try {
      const response = await chatbotService.updateChatbot(form)
      setForm(response.data)
      setSaved('Settings saved.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Settings could not be saved.')
    }
  }

  if (!form) return <p className="text-sm text-secondary-text">{error || 'Loading settings…'}</p>

  return (
    <div className="grid max-w-6xl gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <form onSubmit={saveSettings} className="space-y-5">
        <div>
          <h2 className="text-lg font-bold text-primary-text">Chatbot Settings</h2>
          <p className="mt-1 text-sm text-secondary-text">Configure the chatbot shown on your published websites.</p>
        </div>
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>}
        {saved && <div className="rounded-lg bg-green-50 px-3 py-2 text-xs text-green-700">{saved}</div>}

        <div className="grid gap-4 rounded-xl border border-border bg-surface p-5 sm:grid-cols-2">
          <label className="text-sm font-medium">Chatbot name<input className="form-input mt-1.5" value={form.name} maxLength={100} onChange={(e) => update('name', e.target.value)} /></label>
          <label className="text-sm font-medium">Description<input className="form-input mt-1.5" value={form.description} maxLength={300} onChange={(e) => update('description', e.target.value)} /></label>
          <label className="text-sm font-medium sm:col-span-2">Welcome message<textarea className="form-input mt-1.5 min-h-20" value={form.welcome_message} maxLength={500} onChange={(e) => update('welcome_message', e.target.value)} /></label>
          <label className="text-sm font-medium">Input placeholder<input className="form-input mt-1.5" value={form.placeholder} maxLength={150} onChange={(e) => update('placeholder', e.target.value)} /></label>
          <label className="text-sm font-medium">Launcher text<input className="form-input mt-1.5" value={form.launcher_label} maxLength={50} onChange={(e) => update('launcher_label', e.target.value)} /></label>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-4 text-sm font-semibold">Appearance</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium">Primary color<div className="mt-1.5 flex gap-2"><input type="color" value={form.primary_color} onChange={(e) => update('primary_color', e.target.value)} className="h-10 w-12 rounded border" /><input className="form-input" value={form.primary_color} onChange={(e) => update('primary_color', e.target.value)} /></div></label>
            <label className="text-sm font-medium">Position<select className="form-input mt-1.5" value={form.position} onChange={(e) => update('position', e.target.value)}><option value="bottom-right">Bottom right</option><option value="bottom-left">Bottom left</option></select></label>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-3 text-sm font-semibold">Suggested questions</h3>
          {(form.suggested_questions || []).map((item, index) => (
            <div key={index} className="mb-2 flex gap-2"><input className="form-input" value={item} maxLength={150} onChange={(e) => update('suggested_questions', form.suggested_questions.map((q, i) => i === index ? e.target.value : q))} /><button type="button" className="btn-secondary px-3" onClick={() => update('suggested_questions', form.suggested_questions.filter((_, i) => i !== index))}><Trash2 size={14} /></button></div>
          ))}
          {(form.suggested_questions || []).length < 5 && <button type="button" className="btn-secondary mt-1 text-xs" onClick={() => update('suggested_questions', [...(form.suggested_questions || []), ''])}><Plus size={14} /> Add question</button>}
        </div>

        <div className="rounded-xl border border-border bg-surface p-5">
          <h3 className="mb-3 text-sm font-semibold">Allowed websites</h3>
          <div className="mb-3 flex gap-2"><input className="form-input" value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="https://example.com" /><button type="button" className="btn-secondary" onClick={addDomain}><Plus size={14} /> Add</button></div>
          {(form.allowed_domains || []).map((item) => (
            <div key={item} className="mb-2 flex items-center justify-between rounded-md bg-background px-3 py-2 text-xs"><span>{item}</span><button type="button" onClick={() => update('allowed_domains', form.allowed_domains.filter((origin) => origin !== item))}><Trash2 size={14} /></button></div>
          ))}
        </div>

        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.show_sources} onChange={(e) => update('show_sources', e.target.checked)} /> Show approved source labels</label>
        <button type="submit" className="btn-primary"><Save size={14} /> Save settings</button>
      </form>

      <aside className="rounded-xl border border-border bg-surface p-4 lg:sticky lg:top-6 lg:h-fit">
        <p className="mb-3 text-sm font-semibold">Live preview</p>
        <div className="h-[420px] overflow-hidden rounded-xl border border-border bg-gray-50">
          <div className="px-4 py-3 text-white" style={{ backgroundColor: form.primary_color }}><p className="text-sm font-semibold">{form.name}</p><p className="text-xs opacity-90">{form.description}</p></div>
          <div className="p-3"><div className="max-w-[85%] rounded-2xl bg-white p-3 text-sm shadow-sm">{form.welcome_message}</div></div>
        </div>
      </aside>
    </div>
  )
}
