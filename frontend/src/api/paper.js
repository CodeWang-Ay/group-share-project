import axios from 'axios'

const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const paperApi = {
  // 获取文献列表
  getPapers(params) {
    return axios.get('/api/paper_database/', {
      params,
      headers: getAuthHeaders()
    })
  },

  // 获取文献统计
  getStats(libraryType) {
    return axios.get('/api/paper_database/stats', {
      params: { library_type: libraryType },
      headers: getAuthHeaders()
    })
  },

  // 获取标签列表
  getTags() {
    return axios.get('/api/paper_database/tags', {
      headers: getAuthHeaders()
    })
  },

  // 获取文献详情
  getPaperDetail(paperId, libraryType) {
    return axios.get(`/api/paper_database/${paperId}`, {
      params: { library_type: libraryType },
      headers: getAuthHeaders()
    })
  },

  // 上传文献
  uploadPaper(formData) {
    const token = localStorage.getItem('session_token')
    return axios.post('/api/paper_database/', formData, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 更新文献信息
  updatePaper(paperId, data) {
    return axios.put(`/api/paper_database/${paperId}`, data, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 收藏/取消收藏
  toggleStar(paperId, libraryType) {
    return axios.post(`/api/paper_database/${paperId}/star`,
      { library_type: libraryType },
      { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
  },

  // 更新阅读状态
  updateStatus(paperId, status, libraryType) {
    return axios.put(`/api/paper_database/${paperId}/status`,
      { status, library_type: libraryType },
      { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
  },

  // 删除文献
  deletePaper(paperId, libraryType) {
    return axios.delete(`/api/paper_database/${paperId}`, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      data: { library_type: libraryType }
    })
  },

  // 添加到个人文献库
  addToPersonal(paperId) {
    return axios.post(`/api/paper_database/${paperId}/add-to-personal`, {}, {
      headers: getAuthHeaders()
    })
  },

  // 分享到团队文献库
  shareToTeam(paperId) {
    return axios.post(`/api/paper_database/${paperId}/share-to-team`, {}, {
      headers: getAuthHeaders()
    })
  },

  // 批量收藏
  batchStar(paperIds, star, libraryType) {
    return axios.post('/api/paper_database/batch/star',
      { paper_ids: paperIds, star, library_type: libraryType },
      { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
  },

  // 批量设置标签
  batchSetTags(paperIds, tag, libraryType) {
    return axios.post('/api/paper_database/batch/tags',
      { paper_ids: paperIds, tag, library_type: libraryType },
      { headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' } }
    )
  },

  // 批量删除
  batchDelete(paperIds, libraryType) {
    return axios.delete('/api/paper_database/batch', {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      data: { paper_ids: paperIds, library_type: libraryType }
    })
  },

  // 获取下载URL
  getDownloadUrl(paperId, libraryType) {
    const token = localStorage.getItem('session_token')
    const baseUrl = axios.defaults.baseURL || window.location.origin
    return `${baseUrl}/api/paper_database/${paperId}/download?library_type=${libraryType}${token ? `&session_token=${token}` : ''}`
  },

  // 下载文献
  downloadPaper(paperId, libraryType) {
    const url = this.getDownloadUrl(paperId, libraryType)
    window.open(url, '_blank')
  }
}