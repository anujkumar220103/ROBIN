// Displays uploaded documents and provides document management actions.

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  FileText, Upload, Download, RotateCcw, Trash2, RefreshCw,
  Search, X, ChevronLeft, ChevronRight, Database,
} from 'lucide-react'
import { documentService } from '../services/documentService.js'

const statusStyles = {
  pending: 'bg-gray-100 text-gray-700',
  processing: 'bg-blue-50 text-blue-700',
  ready: 'bg-green-50 text-green-700',
  failed: 'bg-red-50 text-red-700',
  deleting: 'bg-amber-50 text-amber-700',
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / (1024 ** index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

function getErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || 'Invalid request').join(' ')
  }
  return fallback
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadResults, setUploadResults] = useState([])
  const [uploadStage, setUploadStage] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [details, setDetails] = useState(null)
  const pollingRef = useRef(false)

  const load = useCallback(async (showLoading = true) => {
    if (pollingRef.current) return
    if (showLoading) setLoading(true)
    try {
      const [documentResponse, statsResponse] = await Promise.all([
        documentService.getDocuments({
          page,
          page_size: pageSize,
          status: statusFilter || undefined,
          search: search || undefined,
        }),
        documentService.getKnowledgeBaseStats(),
      ])
      setDocuments(documentResponse.data.items)
      setTotal(documentResponse.data.total)
      setStats(statsResponse.data)
      setError('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Documents could not be loaded.')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, search, statusFilter])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    const active = documents.some((item) => ['pending', 'processing', 'deleting'].includes(item.status))
    if (!active) return undefined
    const interval = setInterval(() => {
      pollingRef.current = true
      load(false).finally(() => { pollingRef.current = false })
    }, 4000)
    return () => clearInterval(interval)
  }, [documents, load])

  function submitSearch(event) {
    event.preventDefault()
    setPage(1)
    load()
  }

  function handleFiles(fileList) {
    const files = Array.from(fileList)
    setSelectedFiles(files)
    setUploadResults([])
  }

  async function uploadFiles() {
    if (!selectedFiles.length) return
    setUploading(true)
    setUploadProgress(0)
    setUploadStage('Uploading PDF')
    const results = []
    const uploadedDocumentIds = []
    for (const [index, file] of selectedFiles.entries()) {
      try {
        const response = await documentService.uploadDocument(file)
        uploadedDocumentIds.push(response.data.document.id)
        setUploadStage('Uploading and saving PDF')
        setUploadProgress(Math.round(((index + 0.35) / selectedFiles.length) * 100))
        results.push({ name: file.name, success: true, message: response.data.document.status })
      } catch (err) {
        results.push({
          name: file.name,
          success: false,
          message: getErrorMessage(err, 'Upload failed.'),
        })
      }
      setUploadProgress(Math.round(((index + 1) / selectedFiles.length) * 100))
      setUploadResults([...results])
    }
    if (uploadedDocumentIds.length > 0) {
      setUploadStage('Extracting text and creating chunks')
      setUploadProgress(48)
      for (let attempt = 0; attempt < 180; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000))
        try {
          const response = await documentService.getDocuments({ page: 1, page_size: 100 })
          const uploaded = response.data.items.filter((item) => uploadedDocumentIds.includes(item.id))
          if (uploaded.some((item) => item.status === 'failed')) {
            setUploadStage('Document processing failed')
            setUploadResults((current) => current.map((result) => ({ ...result, success: false })))
            break
          }
          if (uploaded.length === uploadedDocumentIds.length && uploaded.every((item) => item.status === 'ready')) {
            setUploadStage('Generating embeddings and indexing in vector database')
            setUploadProgress(92)
            await new Promise((resolve) => setTimeout(resolve, 400))
            setUploadProgress(100)
            setUploadStage('Knowledge base ready')
            await load()
            break
          }
          setUploadProgress((current) => Math.min(88, current + 2))
          setUploadStage(uploaded.some((item) => item.status === 'processing')
            ? 'Generating embeddings and indexing in vector database'
            : 'Extracting text and creating chunks')
        } catch {
          // Continue polling; the existing load API handles recoverable network errors.
        }
      }
    }
    await load()
    setUploading(false)
  }

  async function downloadDocument(document) {
    try {
      const response = await documentService.downloadDocument(document.id)
      const url = URL.createObjectURL(response.data)
      const anchor = window.document.createElement('a')
      anchor.href = url
      anchor.download = document.original_filename
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.response?.data?.detail || 'PDF download failed.')
    }
  }

  async function retryDocument(documentId) {
    try {
      await documentService.retryDocument(documentId)
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Document retry failed.')
    }
  }

  async function deleteDocument(document) {
    if (!window.confirm(`Delete "${document.original_filename}"? It will be removed from the knowledge base.`)) return
    try {
      await documentService.deleteDocument(document.id)
      setDetails(null)
      await load()
    } catch (err) {
      setError(getErrorMessage(err, 'Document deletion failed.'))
    }
  }

  async function updateVisibility(document) {
    const publish = !document.is_publicly_searchable
    if (publish && !window.confirm('Publish this document to the website chatbot? Its information may be disclosed to public website visitors.')) return
    try {
      await documentService.updateVisibility(document.id, publish)
      await load()
      setDetails((current) => current ? { ...current, is_publicly_searchable: publish } : current)
    } catch (err) {
      setError(getErrorMessage(err, 'Document visibility could not be updated.'))
    }
  }

  const pages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="max-w-5xl">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-primary-text">Documents</h2>
          <p className="text-sm text-secondary-text mt-1">Upload PDFs and manage your company knowledge base.</p>
        </div>
        <button className="btn-primary" onClick={() => setUploadOpen(true)}>
          <Upload size={16} /> Upload PDFs
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          {[
            ['Total documents', stats.total_documents],
            ['Ready', stats.ready_documents],
            ['Processing', stats.processing_documents],
            ['Indexed chunks', stats.total_chunks],
          ].map(([label, value]) => (
            <div key={label} className="border border-border rounded-lg px-4 py-3">
              <p className="text-xs text-secondary-text">{label}</p>
              <p className="text-xl font-semibold text-primary-text mt-1">{value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="bg-surface border border-border rounded-xl">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between p-4 border-b border-border">
          <form onSubmit={submitSearch} className="flex gap-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="form-input pl-9"
                placeholder="Search filename"
              />
            </div>
            <button type="submit" className="btn-secondary text-xs">Search</button>
          </form>
          <div className="flex gap-2">
            <select
              value={statusFilter}
              onChange={(event) => { setStatusFilter(event.target.value); setPage(1) }}
              className="form-input py-2 text-xs"
            >
              <option value="">All statuses</option>
              {Object.keys(statusStyles).map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <button className="btn-secondary px-3" onClick={() => load()} title="Refresh">
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        {error && <div className="mx-4 mt-4 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">{error}</div>}

        {loading ? (
          <div className="p-10 text-center text-sm text-secondary-text">Loading documents…</div>
        ) : documents.length === 0 ? (
          <div className="p-10 text-center">
            <Database size={26} className="mx-auto text-secondary-text mb-3" />
            <p className="text-sm font-medium text-primary-text">No documents yet</p>
            <p className="text-xs text-secondary-text mt-1">Upload a PDF to start building your knowledge base.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-secondary-text border-b border-border">
                  <th className="px-4 py-3 font-medium">Document</th>
                  <th className="px-3 py-3 font-medium">Size</th>
                  <th className="px-3 py-3 font-medium">Pages</th>
                  <th className="px-3 py-3 font-medium">Chunks</th>
                  <th className="px-3 py-3 font-medium">Status</th>
                  <th className="px-3 py-3 font-medium">Website chatbot</th>
                  <th className="px-3 py-3 font-medium">Uploaded</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr key={document.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3">
                      <button onClick={() => setDetails(document)} className="flex items-center gap-2 text-primary-text hover:text-accent">
                        <FileText size={16} className="text-secondary-text" />
                        <span className="max-w-[220px] truncate">{document.original_filename}</span>
                      </button>
                    </td>
                    <td className="px-3 py-3 text-secondary-text">{formatBytes(document.file_size)}</td>
                    <td className="px-3 py-3 text-secondary-text">{document.page_count || '-'}</td>
                    <td className="px-3 py-3 text-secondary-text">{document.chunk_count || '-'}</td>
                    <td className="px-3 py-3">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${statusStyles[document.status]}`}>
                        {document.status}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <button
                        disabled={document.status !== 'ready'}
                        onClick={() => updateVisibility(document)}
                        className={`rounded-full px-2 py-1 text-xs ${document.is_publicly_searchable ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-600'} disabled:cursor-not-allowed disabled:opacity-50`}
                        title={document.status !== 'ready' ? 'Only ready documents can be published' : 'Change website chatbot visibility'}
                      >
                        {document.is_publicly_searchable ? 'Website' : 'Private'}
                      </button>
                    </td>
                    <td className="px-3 py-3 text-secondary-text">{new Date(document.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <button className="p-2 text-secondary-text hover:text-primary-text" title="Download" onClick={() => downloadDocument(document)}>
                          <Download size={15} />
                        </button>
                        {document.status === 'failed' && (
                          <button className="p-2 text-secondary-text hover:text-accent" title="Retry" onClick={() => retryDocument(document.id)}>
                            <RotateCcw size={15} />
                          </button>
                        )}
                        {document.status !== 'processing' && (
                          <button className="p-2 text-secondary-text hover:text-error" title="Delete" onClick={() => deleteDocument(document)}>
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {total > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border text-xs text-secondary-text">
            <span>{total} document{total === 1 ? '' : 's'}</span>
            <div className="flex items-center gap-2">
              <button className="btn-secondary px-2 py-1" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                <ChevronLeft size={14} />
              </button>
              <span>{page} / {pages}</span>
              <button className="btn-secondary px-2 py-1" disabled={page >= pages} onClick={() => setPage(page + 1)}>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {uploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-lg rounded-xl border border-border bg-surface shadow-xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold text-primary-text">Upload PDF documents</h3>
              <button onClick={() => setUploadOpen(false)} className="text-secondary-text"><X size={18} /></button>
            </div>
            <div className="p-5">
              <label
                className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border bg-background"
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => { event.preventDefault(); handleFiles(event.dataTransfer.files) }}
              >
                <Upload size={22} className="text-secondary-text mb-2" />
                <span className="text-sm font-medium text-primary-text">Drop PDF files here</span>
                <span className="mt-1 text-xs text-secondary-text">PDF only · 20 MB maximum per file</span>
                <input type="file" accept="application/pdf,.pdf" multiple className="hidden" onChange={(event) => handleFiles(event.target.files)} />
              </label>
              {selectedFiles.length > 0 && (
                <div className="mt-3 space-y-2">
                  {selectedFiles.map((file) => (
                    <div key={file.name} className="flex justify-between rounded-md bg-background px-3 py-2 text-xs">
                      <span className="truncate text-primary-text">{file.name}</span>
                      <span className="text-secondary-text">{formatBytes(file.size)}</span>
                    </div>
                  ))}
                </div>
              )}
              {uploading && (
                <div className="mt-4 overflow-hidden rounded-xl border border-accent/20 bg-gradient-to-br from-accent/5 via-white to-blue-50 p-4">
                  <div className="flex items-center gap-3">
                    <div className="relative h-11 w-11 shrink-0">
                      <div className="absolute inset-0 rounded-full border-4 border-accent/15"></div>
                      <div className="absolute inset-0 animate-spin rounded-full border-4 border-transparent border-t-accent"></div>
                      <div className="absolute inset-2 rounded-full bg-accent/10"></div>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-primary-text">{uploadStage}</p>
                      <p className="mt-0.5 text-xs text-secondary-text">Please keep this window open while ROBIN prepares the knowledge base.</p>
                    </div>
                    <span className="text-sm font-bold text-accent">{uploadProgress}%</span>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-accent/10">
                    <div
                      className="h-full rounded-full bg-accent transition-all duration-500"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-[11px]">
                    {[
                      ['1', 'Upload'],
                      ['2', 'Chunk'],
                      ['3', 'Vector DB'],
                    ].map(([number, label], index) => {
                      const activeStep = uploadProgress < 55 ? 0 : uploadProgress < 100 ? 1 : 2
                      return (
                        <div
                          key={label}
                          className={`rounded-lg px-2 py-2 text-center font-medium ${
                            index <= activeStep
                              ? 'bg-accent text-white'
                              : 'bg-white text-secondary-text'
                          }`}
                        >
                          {number}. {label}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
              {uploadResults.length > 0 && (
                <div className="mt-3 space-y-2">
                  {uploadResults.map((result) => (
                    <div key={result.name} className={`rounded-md px-3 py-2 text-xs ${result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                      {result.name}: {result.message}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2 border-t border-border px-5 py-4">
              <button className="btn-secondary" disabled={uploading} onClick={() => setUploadOpen(false)}>Cancel</button>
              <button className="btn-primary" disabled={uploading || !selectedFiles.length} onClick={uploadFiles}>
                {uploading ? 'Uploading…' : 'Upload'}
              </button>
            </div>
          </div>
        </div>
      )}

      {details && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface shadow-xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold text-primary-text">Document details</h3>
              <button onClick={() => setDetails(null)} className="text-secondary-text"><X size={18} /></button>
            </div>
            <div className="space-y-3 p-5 text-sm">
              <p><span className="text-secondary-text">Name:</span> <span className="ml-2 text-primary-text">{details.original_filename}</span></p>
              <p><span className="text-secondary-text">Status:</span> <span className="ml-2">{details.status}</span></p>
              <p><span className="text-secondary-text">Pages:</span> <span className="ml-2">{details.page_count}</span></p>
              <p><span className="text-secondary-text">Chunks:</span> <span className="ml-2">{details.chunk_count}</span></p>
              <p><span className="text-secondary-text">Model:</span> <span className="ml-2">{details.embedding_model || '-'}</span></p>
              <p><span className="text-secondary-text">Website chatbot:</span> <span className="ml-2">{details.is_publicly_searchable ? 'Published' : 'Private'}</span></p>
              {details.is_publicly_searchable && (
                <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  This document may be used to answer public website visitors. Do not publish confidential or internal-only documents.
                </p>
              )}
              {details.error_message && <p className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">{details.error_message}</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
