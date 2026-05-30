import api from './dashboard'

export const paperApi = {
  // 获取文献列表
  getPapers(params) {
    return api.get('/paper_database/', { params })
  },

  // 获取文献统计
  getStats(libraryType) {
    return api.get('/paper_database/stats', { params: { library_type: libraryType } })
  },

  // 获取标签列表
  getTags() {
    return api.get('/paper_database/tags')
  },

  // 获取文献详情
  getPaperDetail(paperId, libraryType) {
    return api.get(`/paper_database/${paperId}`, { params: { library_type: libraryType } })
  },

  // 上传文献
  uploadPaper(formData) {
    return api.post('/paper_database/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 更新文献信息
  updatePaper(paperId, data) {
    return api.put(`/paper_database/${paperId}`, data)
  },

  // 收藏/取消收藏
  toggleStar(paperId, libraryType) {
    return api.post(`/paper_database/${paperId}/star`, { library_type: libraryType })
  },

  // 更新阅读状态
  updateStatus(paperId, status, libraryType) {
    return api.put(`/paper_database/${paperId}/status`, { status, library_type: libraryType })
  },

  // 删除文献
  deletePaper(paperId, libraryType) {
    return api.delete(`/paper_database/${paperId}`, { data: { library_type: libraryType } })
  },

  // 添加到个人文献库
  addToPersonal(paperId) {
    return api.post(`/paper_database/${paperId}/add-to-personal`)
  },

  // 分享到团队文献库
  shareToTeam(paperId) {
    return api.post(`/paper_database/${paperId}/share-to-team`)
  },

  // 批量收藏
  batchStar(paperIds, star, libraryType) {
    return api.post('/paper_database/batch/star', { paper_ids: paperIds, star, library_type: libraryType })
  },

  // 批量设置标签
  batchSetTags(paperIds, tag, libraryType) {
    return api.post('/paper_database/batch/tags', { paper_ids: paperIds, tag, library_type: libraryType })
  },

  // 批量删除
  batchDelete(paperIds, libraryType) {
    return api.delete('/paper_database/batch', { data: { paper_ids: paperIds, library_type: libraryType } })
  },

  // 获取下载URL
  getDownloadUrl(paperId, libraryType) {
    return `/api/paper_database/${paperId}/download?library_type=${libraryType}`
  },

  // 下载文献
  downloadPaper(paperId, libraryType) {
    const url = this.getDownloadUrl(paperId, libraryType)
    window.open(url, '_blank')
  }
}