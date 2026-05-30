import api from './dashboard'

export const passwordApi = {
  // 修改密码
  changePassword(oldPassword, newPassword, confirmPassword) {
    return api.put('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: confirmPassword
    })
  }
}