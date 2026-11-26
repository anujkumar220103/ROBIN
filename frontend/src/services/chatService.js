// Handles RAG chat requests and provider status queries.
// Existing Axios instance reuse karte hain — cookies and CSRF headers automatically handle hote hain.

import api from './api.js'

// RAG generation timeout — normal API calls se zyada time lag sakta hai.
const CHAT_TIMEOUT = 90000

export const chatService = {
  /**
   * Submit a question with optional conversation history.
   * Returns grounded answer with source citations.
   */
  askQuestion(question, history = [], abortSignal = null) {
    return api.post(
      '/chat/ask',
      { question, history },
      {
        timeout: CHAT_TIMEOUT,
        signal: abortSignal,
      }
    )
  },

  /**
   * Get safe provider configuration status.
   * API keys expose nahi hote — sirf configured/enabled booleans milte hain.
   */
  getProviderStatus() {
    return api.get('/chat/providers/status')
  },
}
