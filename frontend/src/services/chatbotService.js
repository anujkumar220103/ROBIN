// Handles authenticated chatbot configuration and embed integration APIs.

import api from './api.js'

export const chatbotService = {
  getChatbot() {
    return api.get('/chatbot')
  },
  updateChatbot(payload) {
    return api.patch('/chatbot', payload)
  },
  activateChatbot(payload) {
    return api.post('/chatbot/activate', payload)
  },
  deactivateChatbot() {
    return api.post('/chatbot/deactivate')
  },
  rotatePublicId() {
    return api.post('/chatbot/rotate-id', { confirm: true })
  },
  getEmbedCode() {
    return api.get('/chatbot/embed')
  },
}
