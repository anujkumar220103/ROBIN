// Handles authentication API calls — register, login, logout, and session restore.

import api, { setCsrfToken } from './api.js'

export const authService = {
  async register(data) {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  async login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  async logout() {
    const response = await api.post('/auth/logout')
    return response.data
  },

  // Session restore — app start par call hota hai.
  // /auth/me now returns csrf_token in the body so the in-memory token
  // store is repopulated after every page refresh.
  async getMe() {
    const response = await api.get('/auth/me')
    return response.data
  },

  async updateProfile(data) {
    const response = await api.patch('/auth/me', data)
    // PATCH /auth/me re-issues a fresh CSRF token — keep the store current.
    if (response.data?.csrf_token) {
      setCsrfToken(response.data.csrf_token)
    }
    return response.data
  },
}
