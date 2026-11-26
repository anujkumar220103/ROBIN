// Calls public widget APIs without using the administrator authentication cookie.

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export function getPublicConfig(publicId, embeddingOrigin) {
  return axios.get(`${API_BASE_URL}/public/chatbots/${publicId}/config`, {
    headers: { 'X-Robin-Origin': embeddingOrigin || window.location.origin },
  })
}

export function createPublicSession(publicId, embeddingOrigin) {
  return axios.post(`${API_BASE_URL}/public/chatbots/${publicId}/session`, {}, {
    headers: { 'X-Robin-Origin': embeddingOrigin || window.location.origin },
  })
}

export function askPublicChatbot(publicId, sessionToken, question, history, embeddingOrigin) {
  return axios.post(`${API_BASE_URL}/public/chatbots/${publicId}/ask`, { question, history }, {
    headers: {
      Authorization: `Bearer ${sessionToken}`,
      'X-Robin-Origin': embeddingOrigin || window.location.origin,
    },
  })
}
