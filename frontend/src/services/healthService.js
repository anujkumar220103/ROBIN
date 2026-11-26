// Backend health check API calls.

import api from './api.js'

export const healthService = {
  async getHealth() {
    const response = await api.get('/health')
    return response.data
  },

  async getDatabaseHealth() {
    const response = await api.get('/health/db')
    return response.data
  },
}
