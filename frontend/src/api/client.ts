import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // JWT в httpOnly cookies, не в localStorage
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    // Однократная попытка обновить access-токен по refresh-cookie
    if (error.response?.status === 401 && !original._retried && original.url !== '/auth/login') {
      original._retried = true
      try {
        await axios.post('/api/auth/refresh', null, { withCredentials: true })
        return api(original)
      } catch {
        window.dispatchEvent(new Event('ncaip:unauthorized'))
      }
    }
    return Promise.reject(error)
  },
)
