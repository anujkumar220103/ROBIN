// Handles document upload and management API requests.

import api from './api.js'

export const documentService = {
  async uploadDocument(file, onUploadProgress) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/documents/upload', formData, {
      timeout: 60000,
      onUploadProgress,
    })
  },
  getDocuments(params) {
    return api.get('/documents', { params })
  },
  getDocument(documentId) {
    return api.get(`/documents/${documentId}`)
  },
  async downloadDocument(documentId) {
    return api.get(`/documents/${documentId}/download`, { responseType: 'blob', timeout: 60000 })
  },
  deleteDocument(documentId) {
    return api.delete(`/documents/${documentId}`)
  },
  retryDocument(documentId) {
    return api.post(`/documents/${documentId}/retry`)
  },
  getKnowledgeBaseStats() {
    return api.get('/knowledge-base/stats')
  },
}
