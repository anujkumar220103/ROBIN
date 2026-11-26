// Centralized Axios instance — all backend API calls go through this module.

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// ---------------------------------------------------------------------------
// In-memory CSRF token store
// ---------------------------------------------------------------------------
// document.cookie cannot read cookies set by a different origin (e.g. Render)
// when the frontend is on a different origin (e.g. Vercel). The browser will
// send the cookie back to the backend automatically via withCredentials, but
// JavaScript on the frontend origin cannot read it. We therefore keep the
// CSRF token value in module-level memory, populated from the JSON response
// body of /auth/login and /auth/me. This is safe because:
//   - It is never persisted to localStorage / sessionStorage.
//   - It is cleared on logout.
//   - An attacker on another origin cannot read this memory.
let _csrfToken = null

export function setCsrfToken(token) {
  _csrfToken = token || null
}

export function clearCsrfToken() {
  _csrfToken = null
}

function getCsrfToken() {
  return _csrfToken
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const api = axios.create({
  baseURL: API_BASE_URL,
  // withCredentials: true is required so the browser sends the HTTP-only auth
  // cookie (robin_access_token) on every request. The browser also sends the
  // robin_csrf_token cookie automatically, but we cannot read it from JS here.
  withCredentials: true,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// CSRF token interceptor — attaches X-CSRF-Token header to every
// state-changing request (POST, PUT, PATCH, DELETE).
// The backend validates that the header value matches the CSRF cookie value
// (double-submit cookie pattern). Cross-site scripts cannot set custom
// headers, so this prevents CSRF attacks.
api.interceptors.request.use((config) => {
  const safeMethods = ['get', 'head', 'options']
  if (!safeMethods.includes(config.method?.toLowerCase())) {
    const token = getCsrfToken()
    if (token) {
      config.headers['X-CSRF-Token'] = token
    }
  }
  return config
})

export default api
