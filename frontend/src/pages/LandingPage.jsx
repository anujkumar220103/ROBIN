// Professional SaaS landing page for ROBIN AI.

import { Link } from 'react-router-dom'
import {
  Bot,
  FileText,
  Search,
  MessageSquare,
  Code2,
  ShieldCheck,
  BookOpen,
  ArrowRight,
  ChevronRight,
} from 'lucide-react'

function Navbar() {
  return (
    <nav className="border-b border-border bg-surface/95 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center shrink-0">
            <Bot size={16} className="text-white" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-bold text-primary-text">ROBIN AI</span>
            <span className="text-[9px] text-secondary-text tracking-tight font-medium hidden sm:block">Retrieval-Oriented Bot for Intelligent Navigation</span>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-6 text-sm text-secondary-text">
          <a href="#features" className="hover:text-primary-text transition-colors">Features</a>
          <a href="#how-it-works" className="hover:text-primary-text transition-colors">How It Works</a>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm text-secondary-text hover:text-primary-text transition-colors font-medium">
            Sign In
          </Link>
          <Link to="/register" className="btn-primary text-xs px-3 py-1.5">
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  )
}

function Hero() {
  return (
    <section className="max-w-6xl mx-auto px-4 pt-20 pb-16 text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/20 bg-accent/5 text-accent text-xs font-medium mb-6">
        <span className="w-1.5 h-1.5 rounded-full bg-accent"></span>
        Multi-tenant AI knowledge platform
      </div>

      <h1 className="text-4xl md:text-5xl font-bold text-primary-text tracking-tight leading-tight mb-5">
        Your business knowledge,<br />ready to answer.
      </h1>

      <p className="text-lg text-secondary-text max-w-2xl mx-auto mb-8">
        Turn company documents into intelligent knowledge assistants that provide
        relevant, source-based answers to customers and employees.
      </p>

      <div className="flex items-center justify-center gap-3 flex-wrap">
        <Link to="/register" className="btn-primary px-5 py-2.5">
          Get Started <ArrowRight size={16} />
        </Link>
        <a href="#how-it-works" className="btn-secondary px-5 py-2.5">
          How It Works
        </a>
      </div>

      {/* Product preview — clearly labeled */}
      <div className="mt-14 bg-surface border border-border rounded-xl shadow-sm max-w-3xl mx-auto overflow-hidden">
        <div className="border-b border-border px-4 py-2.5 flex items-center gap-2 bg-background">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-gray-200"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-gray-200"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-gray-200"></span>
          </div>
          <span className="text-xs text-secondary-text ml-2">ROBIN AI — Interface Preview</span>
        </div>
        <div className="p-6 text-left space-y-3">
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
              <span className="text-xs font-semibold text-secondary-text">U</span>
            </div>
            <div className="bg-background border border-border rounded-lg px-4 py-2.5 text-sm text-primary-text max-w-sm">
              What is our refund policy for annual subscriptions?
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <div className="bg-accent/5 border border-accent/20 rounded-lg px-4 py-2.5 text-sm text-primary-text max-w-sm">
              <p className="text-secondary-text text-xs mb-1 font-medium">RAG answer — Phase 5</p>
              AI answer will appear here, grounded in your uploaded documents with source citations.
            </div>
            <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center shrink-0">
              <Bot size={14} className="text-white" />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

const features = [
  {
    icon: FileText,
    title: 'Document-Based Knowledge',
    description: 'Upload company PDFs and build a searchable knowledge base from your actual business content.',
    phase: 'Phase 3',
  },
  {
    icon: ShieldCheck,
    title: 'Company Isolation',
    description: "Each company's knowledge base is completely isolated. Your data never mixes with another tenant's.",
    phase: 'Available',
  },
  {
    icon: Search,
    title: 'Context-Aware Answers',
    description: 'Semantic retrieval finds the most relevant document sections to construct accurate, grounded answers.',
    phase: 'Phase 5',
  },
  {
    icon: BookOpen,
    title: 'Source References',
    description: 'Every answer includes citations from the source documents so users can verify the information.',
    phase: 'Phase 5',
  },
  {
    icon: MessageSquare,
    title: 'Chatbot Customization',
    description: 'Configure your chatbot name, appearance, and welcome message to match your brand.',
    phase: 'Phase 6',
  },
  {
    icon: Code2,
    title: 'Website Integration',
    description: 'Embed your intelligent chatbot on any website with a single JavaScript snippet.',
    phase: 'Phase 6',
  },
]

function Features() {
  return (
    <section id="features" className="bg-background py-20">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-primary-text mb-3">Everything you need</h2>
          <p className="text-secondary-text max-w-xl mx-auto text-sm">
            From document ingestion to intelligent answers — built for real business use cases.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map(({ icon: Icon, title, description, phase }) => (
            <div key={title} className="bg-surface border border-border rounded-xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-lg bg-accent/10 flex items-center justify-center">
                  <Icon size={18} className="text-accent" />
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  phase === 'Available'
                    ? 'bg-success/10 text-success'
                    : 'bg-gray-100 text-secondary-text'
                }`}>
                  {phase}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-primary-text mb-1.5">{title}</h3>
              <p className="text-xs text-secondary-text leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const steps = [
  { number: '1', title: 'Upload Documents', description: 'Upload your company PDF files to build the knowledge base.' },
  { number: '2', title: 'Build Knowledge Base', description: 'ROBIN AI processes documents into a searchable vector index.' },
  { number: '3', title: 'Configure Chatbot', description: 'Set up your chatbot name, appearance, and behavior.' },
  { number: '4', title: 'Integrate Your Site', description: 'Embed the chatbot on your website with one script tag.' },
]

function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 bg-surface">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-primary-text mb-3">How it works</h2>
          <p className="text-secondary-text text-sm max-w-md mx-auto">Four steps from documents to a live intelligent assistant.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((step, i) => (
            <div key={step.number} className="relative">
              <div className="bg-background border border-border rounded-xl p-5">
                <div className="w-8 h-8 rounded-lg bg-accent text-white text-sm font-bold flex items-center justify-center mb-3">
                  {step.number}
                </div>
                <h3 className="text-sm font-semibold text-primary-text mb-1.5">{step.title}</h3>
                <p className="text-xs text-secondary-text leading-relaxed">{step.description}</p>
              </div>
              {i < steps.length - 1 && (
                <div className="hidden lg:flex absolute top-8 -right-2 z-10">
                  <ChevronRight size={16} className="text-border" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="border-t border-border bg-surface py-10">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-md bg-accent flex items-center justify-center">
                <Bot size={13} className="text-white" />
              </div>
              <span className="text-sm font-bold text-primary-text">ROBIN AI</span>
            </div>
            <p className="text-xs text-secondary-text max-w-xs">
              Retrieval-Oriented Bot for Intelligent Navigation.<br />
              Multi-tenant AI knowledge assistant platform.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 text-xs text-secondary-text">
            <div>
              <p className="font-medium text-primary-text mb-2">Product</p>
              <div className="space-y-1.5">
                <a href="#features" className="block hover:text-primary-text transition-colors">Features</a>
                <a href="#how-it-works" className="block hover:text-primary-text transition-colors">How It Works</a>
              </div>
            </div>
            <div>
              <p className="font-medium text-primary-text mb-2">Account</p>
              <div className="space-y-1.5">
                <Link to="/login" className="block hover:text-primary-text transition-colors">Sign In</Link>
                <Link to="/register" className="block hover:text-primary-text transition-colors">Get Started</Link>
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-border mt-8 pt-6">
          <p className="text-xs text-secondary-text">© 2026 ROBIN AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <Footer />
    </div>
  )
}
