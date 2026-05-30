import api from './dashboard'

export const profileApi = {
  // 获取用户资料
  getProfile() {
    return api.get('/user/profile')
  },

  // 更新用户资料
  updateProfile(data) {
    return api.put('/user/profile', data)
  },

  // 上传头像
  uploadAvatar(file) {
    const formData = new FormData()
    formData.append('avatar', file)
    return api.post('/user/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}