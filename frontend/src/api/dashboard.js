import axios from 'axios'
import { useUserStore } from '../stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000  // 增加到 30 秒
})

api.interceptors.request.use(config => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

// 401 响应拦截器：token 过期或无效时自动跳转登录页
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

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