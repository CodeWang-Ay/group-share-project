import api from './dashboard'

export const fileApi = {
  // 获取文件列表
  getFiles(params) {
    return api.get('/files', { params })
  },

  // 获取文件统计
  getStats(params) {
    return api.get('/files/stats', { params })
  },

  // 获取文件详情
  getFileDetail(fileId) {
    return api.get(`/files/${fileId}`)
  },

  // 上传文件
  uploadFile(formData) {
    return api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 更新文件信息
  updateFile(fileId, data) {
    return api.put(`/files/${fileId}`, data)
  },

  // 删除文件
  deleteFile(fileId) {
    return api.delete(`/files/${fileId}`)
  },

  // 获取下载URL
  getDownloadUrl(fileId) {
    return `/api/files/${fileId}/download`
  },

  // 获取预览URL
  getViewUrl(fileId) {
    return `/api/files/${fileId}/view`
  },

  // 下载文件
  async downloadFile(fileId, filename) {
    const response = await api.get(`/files/${fileId}/download`, { responseType: 'blob' })
    const blob = response.data
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