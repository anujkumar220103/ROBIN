// Chatbot settings page — configuration UI preview. Persistence available in Phase 6.

import { Settings } from 'lucide-react'

export default function ChatbotSettingsPage() {
  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-primary-text">Chatbot Settings</h2>
        <p className="text-sm text-secondary-text mt-1">
          Configure your chatbot's name, appearance, and welcome message. Settings
          will become configurable in Phase 6.
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-6">
        <p className="text-sm text-amber-700 font-medium">
          Chatbot configuration is not yet available. This interface will be enabled in Phase 6.
        </p>
      </div>

      <div className="bg-surface border border-border rounded-xl divide-y divide-border opacity-50 pointer-events-none select-none">
        <div className="p-5">
          <label className="block text-sm font-medium text-primary-text mb-1.5">Chatbot Name</label>
          <input disabled className="form-input" placeholder="ROBIN Assistant" />
        </div>
        <div className="p-5">
          <label className="block text-sm font-medium text-primary-text mb-1.5">Welcome Message</label>
          <input disabled className="form-input" placeholder="Hello! How can I help you today?" />
        </div>
        <div className="p-5">
          <label className="block text-sm font-medium text-primary-text mb-1.5">Primary Color</label>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-accent border border-border"></div>
            <input disabled className="form-input w-32" placeholder="#2563EB" />
          </div>
        </div>
        <div className="p-5">
          <button disabled className="btn-primary opacity-50 cursor-not-allowed">
            <Settings size={14} /> Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}
