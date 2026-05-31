import api from './dashboard'

// 获取我的研究进展设置
export const getMySettings = () => api.get('/research_progress/settings')

// 获取我的研究进展列表
export const getMyProgress = (params) => api.get('/research_progress/my', { params })

// 提交研究进展
export const submitProgress = (data) => api.post('/research_progress/submit', data)

// 更新研究进展
export const updateProgress = (id, data) => api.put(`/research_progress/${id}`, data)

// 删除研究进展
export const deleteProgress = (id) => api.delete(`/research_progress/${id}`)

// 获取进展详情
export const getProgressDetail = (id) => api.get(`/research_progress/${id}`)

// 获取团队进展统计
export const getTeamStats = () => api.get('/research_progress/stats')

// 获取团队进展列表
export const getTeamProgress = (params) => api.get('/research_progress/team', { params })

// 发送反馈
export const sendFeedback = (id, feedback) => api.post(`/research_progress/${id}/feedback`, { feedback })

// 批量设置提交周期
export const batchSetSettings = (data) => api.post('/research_progress/settings/batch', data)

// 上传文件
export const uploadFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 获取文件下载URL - 需要完整的 URL
import { SERVER_URL } from '../config'

export const getFileDownloadUrl = (filename) => `${SERVER_URL}/api/files/download/${encodeURIComponent(filename)}`

// 删除文件（按文件名）
export const deleteFileByName = (filename) => api.delete(`/files/by_filename/${encodeURIComponent(filename)}`)