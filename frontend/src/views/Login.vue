<template>
  <div class="bg-gray-50 min-h-screen flex items-center justify-center p-4">
    <!-- 登录面板 -->
    <div class="w-full max-w-md">
      <div class="bg-white rounded-xl p-8 shadow-lg shadow-gray-200/50 text-center">
        <!-- Logo -->
        <div class="w-20 h-20 bg-primary rounded-full flex justify-center items-center mx-auto mb-6">
          <i class="fa fa-flask text-white text-3xl"></i>
        </div>

        <!-- 标题 -->
        <h2 class="text-primary text-xl font-bold mb-8">用户登录</h2>

        <!-- 用户名 -->
        <div class="mb-5 text-left">
          <label class="block text-sm text-gray-600 mb-2">用户名</label>
          <input type="text" v-model="username" @keypress.enter="focusPassword"
                 class="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                 placeholder="请输入用户名">
        </div>

        <!-- 密码 -->
        <div class="mb-6 text-left">
          <label class="block text-sm text-gray-600 mb-2">密码</label>
          <div class="relative">
            <input :type="showPassword ? 'text' : 'password'" v-model="password" @keypress.enter="handleLogin"
                   class="w-full px-4 py-3 pr-12 border border-gray-200 rounded-lg bg-gray-50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                   placeholder="请输入密码">
            <button @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-primary">
              <i :class="showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"></i>
            </button>
          </div>
        </div>

        <!-- 按钮组 -->
        <div class="flex gap-4">
          <button @click="handleLogin" :disabled="loading"
                  class="flex-1 bg-primary text-white py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <span v-if="!loading">登录</span>
            <span v-else class="flex items-center justify-center gap-2">
              <i class="fa fa-spinner fa-spin"></i>
              <span>登录中...</span>
            </span>
          </button>
          <button @click="goToRegister"
                  class="flex-1 bg-white text-primary border border-primary py-3 rounded-lg font-medium hover:bg-primary/5 transition-colors">
            注册新账号
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import axios from 'axios'

const userStore = useUserStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)

// 检查是否已登录
onMounted(async () => {
  const sessionToken = localStorage.getItem('session_token')
  if (sessionToken) {
    try {
      const res = await axios.get('/api/auth/session-status', {
        headers: { Authorization: `Bearer ${sessionToken}` }
      })
      if (res.data.success && res.data.data?.authenticated) {
        // 已登录，跳转到首页
        window.location.href = `/?session_token=${sessionToken}`
      } else {
        // 会话无效，清除
        localStorage.removeItem('session_token')
        localStorage.removeItem('user_info')
      }
    } catch (e) {
      localStorage.removeItem('session_token')
      localStorage.removeItem('user_info')
    }
  }
})

function focusPassword() {
  const passwordInput = document.querySelector('input[type="password"], input[type="text"]')
  if (passwordInput) passwordInput.focus()
}

async function handleLogin() {
  if (!username.value.trim()) {
    window.$toast?.('请输入用户名', 'error')
    return
  }
  if (!password.value.trim()) {
    window.$toast?.('请输入密码', 'error')
    return
  }

  loading.value = true

  try {
    const res = await axios.post('/api/auth/login', {
      username: username.value.trim(),
      password: password.value.trim()
    })

    if (res.data.success && res.data.session_token) {
      // 保存 session_token
      localStorage.setItem('session_token', res.data.session_token)
      localStorage.setItem('user_info', JSON.stringify({ username: username.value.trim() }))
      userStore.setToken(res.data.session_token)

      window.$toast?.('登录成功，正在跳转...', 'success')

      // 跳转到首页
      setTimeout(() => {
        window.location.href = `/?session_token=${res.data.session_token}`
      }, 500)
    } else {
      window.$toast?.(res.data.message || '登录失败', 'error')
    }
  } catch (e) {
    const message = e.response?.data?.message || '网络错误，请稍后重试'
    window.$toast?.(message, 'error')
  } finally {
    loading.value = false
  }
}

function goToRegister() {
  window.location.href = '/register'
}
</script>