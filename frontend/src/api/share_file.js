import axios from 'axios'

const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const fileApi = {
  // 获取文件列表
  getFiles(params) {
    return axios.get('/api/files', {
      params,
      headers: getAuthHeaders()
    })
  },

  // 获取文件统计
  getStats(params) {
    return axios.get('/api/files/stats', {
      params,
      headers: getAuthHeaders()
    })
  },

  // 获取文件详情
  getFileDetail(fileId) {
    return axios.get(`/api/files/${fileId}`, {
      headers: getAuthHeaders()
    })
  },

  // 上传文件
  uploadFile(formData) {
    const token = localStorage.getItem('session_token')
    return axios.post('/api/files/upload', formData, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 更新文件信息
  updateFile(fileId, data) {
    return axios.put(`/api/files/${fileId}`, data, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 删除文件
  deleteFile(fileId) {
    return axios.delete(`/api/files/${fileId}`, {
      headers: getAuthHeaders()
    })
  },

  // 获取下载URL
  getDownloadUrl(fileId) {
    const token = localStorage.getItem('session_token')
    const baseUrl = axios.defaults.baseURL || ''
    return `${baseUrl}/api/files/${fileId}/download${token ? `?token=${token}` : ''}`
  },

  // 获取预览URL
  getViewUrl(fileId) {
    const baseUrl = axios.defaults.baseURL || ''
    return `${baseUrl}/api/files/${fileId}/view`
  },

  // 下载文件（通过fetch API处理认证）
  async downloadFile(fileId, filename) {
    const token = localStorage.getItem('session_token')
    const baseUrl = axios.defaults.baseURL || window.location.origin
    const url = `${baseUrl}/api/files/${fileId}/download`

    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })

    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
}