import axios from 'axios'

const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const memberApi = {
  // 获取成员列表
  getMembers(params) {
    return axios.get('/api/members', {
      params,
      headers: getAuthHeaders()
    })
  },

  // 获取统计信息
  getStats() {
    return axios.get('/api/members/stats', {
      headers: getAuthHeaders()
    })
  },

  // 获取成员详情
  getMemberDetail(memberId) {
    return axios.get(`/api/members/${memberId}`, {
      headers: getAuthHeaders()
    })
  },

  // 添加成员
  addMember(data) {
    return axios.post('/api/members', data, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 更新成员信息
  updateMember(memberId, data) {
    return axios.put(`/api/members/${memberId}`, data, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 删除成员
  deleteMember(memberId) {
    return axios.delete(`/api/members/${memberId}`, {
      headers: getAuthHeaders()
    })
  },

  // 重置密码
  resetPassword(memberId, password) {
    return axios.put(`/api/members/${memberId}/reset-password`, { password }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 更新状态
  updateStatus(memberId, status) {
    return axios.put(`/api/members/${memberId}/status`, { status }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 批量更新角色
  batchUpdateRole(userIds, role) {
    return axios.post('/api/users/batch-update-role', { user_ids: userIds, role }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 批量更新状态
  batchUpdateStatus(userIds, status) {
    return axios.post('/api/users/batch-update-status', { user_ids: userIds, status }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 批量删除
  batchDelete(userIds) {
    return axios.post('/api/users/batch-delete', { user_ids: userIds }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 发送留言
  sendMessage(receiverId, title, content) {
    return axios.post('/api/messages/send', { receiver_id: receiverId, title, content }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 获取留言列表
  getMessages() {
    return axios.get('/api/messages', {
      headers: getAuthHeaders()
    })
  },

  // 标记留言已读
  markMessageRead(messageId) {
    return axios.put(`/api/messages/${messageId}/read`, {}, {
      headers: getAuthHeaders()
    })
  }
}