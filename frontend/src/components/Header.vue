<template>
  <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center">
          <button @click="toggleSidebar" class="lg:hidden p-2 rounded-lg hover:bg-gray-100 mr-2">
            <i class="fa fa-bars text-gray-600"></i>
          </button>
          <div class="flex items-center gap-2">
            <i class="fa fa-flask text-primary text-2xl"></i>
            <span class="hidden sm:inline-block text-xl font-semibold">智能计算实验室</span>
          </div>
        </div>

        <div class="flex items-center gap-2 sm:gap-4">
          <div class="relative hidden md:block">
            <input type="text" placeholder="搜索文献、汇报材料..."
                   class="py-2 pl-10 pr-4 rounded-lg bg-gray-100 focus:ring-2 focus:ring-primary/30 w-48 lg:w-64">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
          </div>

          <div class="relative p-2 rounded-full hover:bg-gray-100">
            <i class="fa fa-bell-o text-gray-600"></i>
            <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </div>

          <div class="relative group">
            <div class="flex items-center gap-2 cursor-pointer">
              <img :src="avatarUrl" class="w-8 h-8 rounded-full border-2 border-white shadow-sm">
              <span class="hidden md:inline-block font-medium">{{ userStore.username }}</span>
              <i class="fa fa-chevron-down text-xs text-gray-500"></i>
            </div>
            <div class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
              <div class="px-4 py-2 border-b border-gray-100">
                <p class="font-medium">{{ userStore.username }}</p>
                <p class="text-xs text-gray-500">{{ userStore.roleText }}</p>
              </div>
              <a href="/user_profile" class="block px-4 py-2 text-sm hover:bg-gray-100">
                <i class="fa fa-user-o mr-2 text-gray-500"></i>个人资料
              </a>
              <a href="/edit_password" class="block px-4 py-2 text-sm hover:bg-gray-100">
                <i class="fa fa-key mr-2 text-gray-500"></i>修改密码
              </a>
            </div>
          </div>

          <button @click="logout" class="hidden sm:flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg">
            <i class="fa fa-sign-out"></i>
            <span>退出登录</span>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../stores/user'
import { authApi } from '../api/dashboard'

const userStore = useUserStore()
const sidebarVisible = defineModel()

// 头像URL处理：如果有avatar就用，否则生成默认头像
const avatarUrl = computed(() => {
  if (userStore.avatar) {
    // 如果是相对路径，加上后端地址
    if (userStore.avatar.startsWith('/uploads')) {
      return `http://localhost:8081${userStore.avatar}`
    }
    return userStore.avatar
  }
  // 使用UI Avatars生成默认头像
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(userStore.username || 'User')}&background=2563eb&color=fff&size=128`
})

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

async function logout() {
  try {
    await authApi.logout()
    userStore.clear()
    window.location.href = 'http://localhost:8081/login'
  } catch (e) {
    userStore.clear()
    window.location.href = 'http://localhost:8081/login'
  }
}
</script>