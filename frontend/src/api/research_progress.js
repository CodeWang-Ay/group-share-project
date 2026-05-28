import axios from 'axios'

const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 获取我的研究进展设置
export const getMySettings = () => axios.get('/api/research_progress/settings', {
  headers: getAuthHeaders()
})

// 获取我的研究进展列表
export const getMyProgress = (params) => axios.get('/api/research_progress/my', {
  params,
  headers: getAuthHeaders()
})

// 提交研究进展
export const submitProgress = (data) => axios.post('/api/research_progress/submit', data, {
  headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
})

// 更新研究进展
export const updateProgress = (id, data) => axios.put(`/api/research_progress/${id}`, data, {
  headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
})

// 删除研究进展
export const deleteProgress = (id) => axios.delete(`/api/research_progress/${id}`, {
  headers: getAuthHeaders()
})

// 获取进展详情
export const getProgressDetail = (id) => axios.get(`/api/research_progress/${id}`, {
  headers: getAuthHeaders()
})

// 获取团队进展统计
export const getTeamStats = () => axios.get('/api/research_progress/stats', {
  headers: getAuthHeaders()
})

// 获取团队进展列表
export const getTeamProgress = (params) => axios.get('/api/research_progress/team', {
  params,
  headers: getAuthHeaders()
})

// 发送反馈
export const sendFeedback = (id, feedback) => axios.post(`/api/research_progress/${id}/feedback`, { feedback }, {
  headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
})

// 批量设置提交周期
export const batchSetSettings = (data) => axios.post('/api/research_progress/settings/batch', data, {
  headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
})

// 上传文件
export const uploadFile = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return axios.post('/api/files/upload', formData, {
    headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
  })
}

// 获取文件下载URL
export const getFileDownloadUrl = (filename) => `/api/files/download/${encodeURIComponent(filename)}`