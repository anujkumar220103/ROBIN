// Website integration page — explains the future embed process. Available in Phase 6.

import { Code2, Globe, Zap } from 'lucide-react'

const steps = [
  {
    icon: Zap,
    title: 'Configure your chatbot',
    description: 'Set up your chatbot name, appearance, and knowledge base in Chatbot Settings.',
  },
  {
    icon: Code2,
    title: 'Get your embed code',
    description: 'Copy the generated JavaScript snippet from this page (available in Phase 6).',
  },
  {
    icon: Globe,
    title: 'Add to your website',
    description: 'Paste the snippet before the </body> tag on any page where you want the chatbot.',
  },
]

export default function IntegrationPage() {
  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-primary-text">Website Integration</h2>
        <p className="text-sm text-secondary-text mt-1">
          Embed your ROBIN AI chatbot on any website using a JavaScript snippet.
          Integration will be available in Phase 6.
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-6">
        <p className="text-sm text-amber-700 font-medium">
          Website integration is not yet available. The embed code will be generated in Phase 6
          after chatbot configuration is complete.
        </p>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-semibold text-primary-text mb-3">How integration works</h3>
        <div className="space-y-3">
          {steps.map(({ icon: Icon, title, description }) => (
            <div key={title} className="bg-surface border border-border rounded-xl p-4 flex gap-4">
              <div className="w-9 h-9 rounded-lg bg-background flex items-center justify-center shrink-0">
                <Icon size={18} className="text-secondary-text" />
              </div>
              <div>
                <p className="text-sm font-medium text-primary-text">{title}</p>
                <p className="text-xs text-secondary-text mt-0.5">{description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-surface border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-primary-text">Embed Code</h3>
          <span className="text-xs bg-gray-100 text-secondary-text px-2 py-0.5 rounded-full">Phase 6</span>
        </div>
        <div className="bg-background rounded-lg border border-border p-4 font-mono text-xs text-secondary-text">
          {`<!-- Embed code will appear here after chatbot configuration in Phase 6 -->`}
        </div>
        <button disabled className="btn-primary text-xs mt-3 opacity-50 cursor-not-allowed">
          Copy embed code
        </button>
      </div>
    </div>
  )
}
