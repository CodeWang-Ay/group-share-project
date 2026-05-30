import api from './dashboard'

export const taskApi = {
  // 获取任务列表
  getTasks(params) {
    return api.get('/research_tasks', { params })
  },

  // 获取任务统计
  getStats() {
    return api.get('/research_tasks/stats')
  },

  // 获取任务详情
  getTaskDetail(taskId) {
    return api.get(`/research_tasks/${taskId}`)
  },

  // 创建任务
  createTask(data) {
    return api.post('/research_tasks', data)
  },

  // 更新任务
  updateTask(taskId, data) {
    return api.put(`/research_tasks/${taskId}`, data)
  },

  // 更新任务进度
  updateProgress(taskId, progress) {
    return api.put(`/research_tasks/${taskId}/progress`, { progress })
  },

  // 删除任务
  deleteTask(taskId) {
    return api.delete(`/research_tasks/${taskId}`)
  }
}