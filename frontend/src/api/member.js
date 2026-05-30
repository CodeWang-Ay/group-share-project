import api from './dashboard'

export const memberApi = {
  // 获取成员列表
  getMembers(params) {
    return api.get('/members', { params })
  },

  // 获取统计信息
  getStats() {
    return api.get('/members/stats')
  },

  // 获取成员详情
  getMemberDetail(memberId) {
    return api.get(`/members/${memberId}`)
  },

  // 添加成员
  addMember(data) {
    return api.post('/members', data)
  },

  // 更新成员信息
  updateMember(memberId, data) {
    return api.put(`/members/${memberId}`, data)
  },

  // 删除成员
  deleteMember(memberId) {
    return api.delete(`/members/${memberId}`)
  },

  // 重置密码
  resetPassword(memberId, password) {
    return api.put(`/members/${memberId}/reset-password`, { password })
  },

  // 更新状态
  updateStatus(memberId, status) {
    return api.put(`/members/${memberId}/status`, { status })
  },

  // 批量更新角色
  batchUpdateRole(userIds, role) {
    return api.post('/users/batch-update-role', { user_ids: userIds, role })
  },

  // 批量更新状态
  batchUpdateStatus(userIds, status) {
    return api.post('/users/batch-update-status', { user_ids: userIds, status })
  },

  // 批量删除
  batchDelete(userIds) {
    return api.post('/users/batch-delete', { user_ids: userIds })
  },

  // 发送留言
  sendMessage(receiverId, title, content) {
    return api.post('/messages/send', { receiver_id: receiverId, title, content })
  },

  // 获取留言列表
  getMessages() {
    return api.get('/messages')
  },

  // 标记留言已读
  markMessageRead(messageId) {
    return api.put(`/messages/${messageId}/read`)
  }
}