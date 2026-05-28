import api from './dashboard'

export const meetingApi = {
  getStats() {
    return api.get('/meetings/stats')
  },

  getList(params = {}) {
    return api.get('/meetings', { params })
  },

  getDetail(id) {
    return api.get(`/meetings/${id}`)
  },

  create(data) {
    return api.post('/meetings', data)
  },

  update(id, data) {
    return api.put(`/meetings/${id}`, data)
  },

  delete(id) {
    return api.delete(`/meetings/${id}`)
  },

  downloadFile(fileId) {
    return api.get(`/meeting_files/${fileId}/download`, { responseType: 'blob' })
  },

  // 搜索成员（用于汇报人选择）
  searchMembers(keyword) {
    return api.get('/members', { params: { keyword, per_page: 20 } })
  }
}