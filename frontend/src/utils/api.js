import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API endpoints
export const apiService = {
  // Health check
  checkHealth: async () => {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      throw error
    }
  },

  // Get service status
  getServicesStatus: async () => {
    try {
      const response = await api.get('/services')
      return response.data
    } catch (error) {
      throw error
    }
  },

  // Submit job match request
  matchJob: async (jobDescription, topK = 10) => {
    try {
      const response = await api.post('/api/v1/match', {
        job_description: jobDescription,
        top_k: topK,
      })
      return response.data
    } catch (error) {
      throw error
    }
  },

  // Get analytics/stats
  getStats: async () => {
    try {
      const response = await api.get('/api/v1/stats')
      return response.data
    } catch (error) {
      throw error
    }
  },
}

export default api
