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

export const materialApi = {
  // 获取组会材料列表
  getMeetings(params) {
    return api.get('/materials/meetings', { params })
  },

  // 获取汇报人列表
  getPresenters(meetingId) {
    return api.get(`/meetings/${meetingId}/presenters`)
  },

  // 确认参会
  confirmAttendance(presenterId) {
    return api.put(`/materials/${presenterId}/confirm`)
  },

  // 获取汇报人已上传文件
  getFiles(presenterId) {
    return api.get(`/materials/${presenterId}/files`)
  },

  // 上传文件
  uploadFile(presenterId, meetingId, file) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('presenter_id', presenterId)
    formData.append('meeting_id', meetingId)
    return api.post(`/materials/${presenterId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 下载文件
  downloadFile(fileId) {
    return api.get(`/files/${fileId}/download`, { responseType: 'blob' })
  },

  // 删除文件
  deleteFile(fileId) {
    return api.delete(`/files/${fileId}`)
  }
}