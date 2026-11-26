// Handles authentication API calls — register, login, logout, and session restore.

import api from './api.js'

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
  // Agar valid cookie hai to user aur company info milti hai.
  async getMe() {
    const response = await api.get('/auth/me')
    return response.data
  },

  async updateProfile(data) {
    const response = await api.patch('/auth/me', data)
    return response.data
  },
}
