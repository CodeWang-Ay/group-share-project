import axios from 'axios'

const getAuthHeaders = () => {
  const token = localStorage.getItem('session_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const taskApi = {
  // 获取任务列表
  getTasks(params) {
    return axios.get('/api/research_tasks', {
      params,
      headers: getAuthHeaders()
    })
  },

  // 获取任务统计
  getStats() {
    return axios.get('/api/research_tasks/stats', {
      headers: getAuthHeaders()
    })
  },

  // 获取任务详情
  getTaskDetail(taskId) {
    return axios.get(`/api/research_tasks/${taskId}`, {
      headers: getAuthHeaders()
    })
  },

  // 创建任务
  createTask(data) {
    return axios.post('/api/research_tasks', data, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 更新任务
  updateTask(taskId, data) {
    return axios.put(`/api/research_tasks/${taskId}`, data, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 更新任务进度
  updateProgress(taskId, progress) {
    return axios.put(`/api/research_tasks/${taskId}/progress`, { progress }, {
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
  },

  // 删除任务
  deleteTask(taskId) {
    return axios.delete(`/api/research_tasks/${taskId}`, {
      headers: getAuthHeaders()
    })
  }
}