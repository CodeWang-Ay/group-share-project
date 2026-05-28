<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <Toast />
    <Header v-model="sidebarVisible" />
    <main class="flex-1 flex">
      <Sidebar v-model="sidebarVisible" />
      <router-view />
    </main>
    <footer class="bg-white border-t border-gray-200 py-4">
      <div class="container mx-auto px-4 text-center text-sm text-gray-500">
        <p>© 2026 智能计算实验室 - 研究生组会管理系统</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from './stores/user'
import { authApi } from './api/dashboard'
import Header from './components/Header.vue'
import Sidebar from './components/Sidebar.vue'
import Toast from './components/Toast.vue'

const userStore = useUserStore()
const sidebarVisible = ref(false)

// 从 URL 参数获取 session_token
const urlParams = new URLSearchParams(window.location.search)
const sessionToken = urlParams.get('session_token')
if (sessionToken) {
  userStore.setToken(sessionToken)
  const url = new URL(window.location)
  url.searchParams.delete('session_token')
  window.history.replaceState({}, document.title, url.toString())
}

// 获取用户信息
onMounted(async () => {
  if (userStore.token && !userStore.username) {
    try {
      const res = await authApi.getMe()
      if (res.data.success && res.data.data.user) {
        userStore.setUserInfo(res.data.data.user)
      }
    } catch (e) {
      console.error('获取用户信息失败:', e)
    }
  }
})
</script>