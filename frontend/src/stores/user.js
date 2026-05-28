import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('session_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || '{}'))

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value.username || '')
  const role = computed(() => userInfo.value.role || 'student')
  const avatar = computed(() => userInfo.value.avatar || '')
  const userId = computed(() => userInfo.value.id || 0)

  const roleText = computed(() => {
    if (role.value === 'admin') return '管理员'
    if (role.value === 'teacher') return '导师'
    return '学生'
  })

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('session_token', newToken)
  }

  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('user_info', JSON.stringify(info))
  }

  function clear() {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('session_token')
    localStorage.removeItem('user_info')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    username,
    role,
    avatar,
    userId,
    roleText,
    setToken,
    setUserInfo,
    clear
  }
})