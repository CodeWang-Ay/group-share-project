import axios from 'axios'
import { useUserStore } from '../stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

api.interceptors.request.use(config => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

export const dashboardApi = {
  getStats() {
    return api.get('/dashboard/stats')
  },
  getUpcoming() {
    return api.get('/dashboard/upcoming')
  },
  getRecentFiles() {
    return api.get('/dashboard/recent_files')
  },
  getRecentPapers() {
    return api.get('/dashboard/recent_papers')
  },
  getRecentProgress() {
    return api.get('/dashboard/recent_progress')
  }
}

export const authApi = {
  logout() {
    return api.post('/auth/logout')
  },
  getMe() {
    return api.get('/auth/me')
  }
}

export default api