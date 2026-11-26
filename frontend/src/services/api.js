// Centralized Axios instance — all backend API calls go through this module.

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  // withCredentials: true is required so the browser sends the HTTP-only auth cookie.
  // HTTP-only cookie ko JavaScript directly read nahi kar sakti.
  // Browser authenticated requests ke saath cookie automatically bhejta hai.
  withCredentials: true,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// CSRF token interceptor — har state-changing request mein CSRF header add karta hai.
// CSRF cookie JavaScript read kar sakta hai, aur use X-CSRF-Token header mein bhejta hai.
// Cross-site script ye header set nahi kar sakta, isliye CSRF attack prevent hota hai.
api.interceptors.request.use((config) => {
  const safeMethods = ['get', 'head', 'options']
  if (!safeMethods.includes(config.method?.toLowerCase())) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  return config
})

function getCsrfToken() {
  const name = 'robin_csrf_token='
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const c = cookie.trim()
    if (c.startsWith(name)) {
      return c.substring(name.length)
    }
  }
  return null
}

export default api
