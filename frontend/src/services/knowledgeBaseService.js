// Handles semantic knowledge base search requests.

import api from './api.js'

export const knowledgeBaseService = {
  search(query, topK = 5, documentId = null) {
    return api.post('/knowledge-base/search', {
      query,
      top_k: topK,
      document_id: documentId,
    })
  },
}
