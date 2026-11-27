// Calls public widget APIs without using the administrator authentication cookie.
// Uses a dedicated axios instance — intentionally separate from api.js so it
// never attaches auth cookies (withCredentials) or the CSRF token header.
// This avoids triggering blocked cross-origin credential requests in the iframe.

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// Dedicated instance for public chatbot endpoints only.
// No withCredentials, no CSRF interceptors, 30-second timeout to accommodate
// LLM inference latency without hanging indefinitely in a cross-origin iframe.
const publicApi = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: false,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export function getPublicConfig(publicId, embeddingOrigin) {
  return publicApi.get(`/public/chatbots/${publicId}/config`, {
    headers: { 'X-Robin-Origin': embeddingOrigin || window.location.origin },
  })
}

export function createPublicSession(publicId, embeddingOrigin) {
  return publicApi.post(`/public/chatbots/${publicId}/session`, {}, {
    headers: { 'X-Robin-Origin': embeddingOrigin || window.location.origin },
  })
}

export function askPublicChatbot(publicId, sessionToken, question, history, embeddingOrigin) {
  return publicApi.post(
    `/public/chatbots/${publicId}/ask`,
    { question, history },
    {
      headers: {
        Authorization: `Bearer ${sessionToken}`,
        'X-Robin-Origin': embeddingOrigin || window.location.origin,
      },
    },
  )
}
