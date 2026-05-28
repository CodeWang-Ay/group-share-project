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

export const recordApi = {
  // 获取组会列表（已召开的）
  getMeetings(params) {
    return api.get('/meetings', { params })
  },

  // 获取组会详情
  getMeetingDetail(meetingId) {
    return api.get(`/meetings/${meetingId}`)
  },

  // 更新会议纪要
  updateMinutes(meetingId, minutes) {
    return api.put(`/meetings/${meetingId}`, { minutes })
  },

  // 获取组会统计
  getStats() {
    return api.get('/meetings/stats')
  },

  // 获取汇报人材料
  getPresenterFiles(presenterId) {
    return api.get(`/materials/${presenterId}/files`)
  },

  // 下载文件
  downloadFile(fileId) {
    return api.get(`/meeting_files/${fileId}/download`, { responseType: 'blob' })
  }
}