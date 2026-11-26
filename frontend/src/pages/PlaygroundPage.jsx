// Provides a semantic search interface for testing the company knowledge base.

import { useState } from 'react'
import { Search, FileText, Loader2 } from 'lucide-react'
import { knowledgeBaseService } from '../services/knowledgeBaseService.js'

export default function PlaygroundPage() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState('')

  async function search(event) {
    event.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setSearched(true)
    try {
      const response = await knowledgeBaseService.search(query.trim(), topK)
      setResults(response.data.results)
    } catch (err) {
      setResults([])
      setError(err.response?.data?.detail || 'Semantic search could not be completed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-5">
        <h2 className="text-lg font-bold text-primary-text">Knowledge Base Search</h2>
        <p className="text-sm text-secondary-text mt-1">
          Search retrieves relevant passages from your uploaded documents. It does not generate an AI answer.
        </p>
      </div>

      <form onSubmit={search} className="flex gap-3 mb-5">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="form-input pl-9"
            placeholder="Search your knowledge base"
            maxLength={1000}
          />
        </div>
        <select value={topK} onChange={(event) => setTopK(Number(event.target.value))} className="form-input w-24">
          {[1, 3, 5, 10, 20].map((value) => (
            <option key={value} value={value}>Top {value}</option>
          ))}
        </select>
        <button type="submit" className="btn-primary" disabled={loading || !query.trim()}>
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          Search
        </button>
      </form>

      {error && <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 mb-4">{error}</div>}

      {loading ? (
        <div className="flex min-h-52 items-center justify-center text-sm text-secondary-text">
          <Loader2 size={18} className="animate-spin mr-2" /> Searching…
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-3">
          {results.map((result) => (
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
                  Cosine similarity: {result.similarity.toFixed(3)}
                </span>
              </div>
              <p className="text-sm leading-6 text-primary-text whitespace-pre-wrap">{result.text}</p>
            </article>
          ))}
        </div>
      ) : searched ? (
        <div className="rounded-xl border border-border p-10 text-center">
          <p className="text-sm font-medium text-primary-text">No relevant chunks found</p>
          <p className="mt-1 text-xs text-secondary-text">Upload and index documents, then try a different query.</p>
        </div>
      ) : null}
    </div>
  )
}
