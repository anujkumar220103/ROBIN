// Company profile API calls.

import api from './api.js'

export const companyService = {
  async getMyCompany() {
    const response = await api.get('/company/me')
    return response.data
  },

  async updateCompany(data) {
    const response = await api.patch('/company/me', data)
    return response.data
  },
}
