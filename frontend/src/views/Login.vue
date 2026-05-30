<template>
  <div class="min-h-screen flex relative overflow-hidden">
    <!-- 全屏背景图片 -->
    <img :src="bgImage" class="fixed inset-0 w-full h-full object-cover" alt="background">
    <!-- 科技光效点缀 -->
    <div class="fixed inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-transparent"></div>
    <div class="fixed top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-purple-400 to-transparent opacity-60"></div>

    <!-- 左侧品牌区域 (60%) -->
    <div class="hidden lg:flex lg:w-[60%] relative z-10 flex-col">
      <div class="flex flex-col justify-between h-full px-16 py-12 text-white">
        <!-- 顶部品牌标识 -->
        <div>
          <div class="flex items-center gap-4 mb-6">
            <div class="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <i class="fa fa-users text-3xl"></i>
            </div>
            <div>
              <div class="text-3xl font-bold tracking-wide">组会管理系统</div>
              <div class="text-sm text-white/70 tracking-[0.2em] mt-1">GROUP MEETING MANAGEMENT SYSTEM</div>
            </div>
          </div>
          <div class="text-lg text-white/60 font-light mt-4">高效协作 · 有序管理 · 智慧组会</div>
        </div>

        <!-- 中景场景元素（由背景图片承载） -->

        <!-- 底部功能亮点区 -->
        <div>
          <!-- 四个功能图标 -->
          <div class="flex gap-10 mb-8">
            <div class="flex flex-col items-center">
              <div class="w-14 h-14 bg-white/15 rounded-xl flex items-center justify-center mb-3 backdrop-blur-sm hover:bg-white/25 transition-colors">
                <i class="fa fa-calendar text-xl"></i>
              </div>
              <span class="text-sm text-white/80">组会计划</span>
            </div>
            <div class="flex flex-col items-center">
              <div class="w-14 h-14 bg-white/15 rounded-xl flex items-center justify-center mb-3 backdrop-blur-sm hover:bg-white/25 transition-colors">
                <i class="fa fa-users text-xl"></i>
              </div>
              <span class="text-sm text-white/80">协作共享</span>
            </div>
            <div class="flex flex-col items-center">
              <div class="w-14 h-14 bg-white/15 rounded-xl flex items-center justify-center mb-3 backdrop-blur-sm hover:bg-white/25 transition-colors">
                <i class="fa fa-line-chart text-xl"></i>
              </div>
              <span class="text-sm text-white/80">进度跟踪</span>
            </div>
            <div class="flex flex-col items-center">
              <div class="w-14 h-14 bg-white/15 rounded-xl flex items-center justify-center mb-3 backdrop-blur-sm hover:bg-white/25 transition-colors">
                <i class="fa fa-shield text-xl"></i>
              </div>
              <span class="text-sm text-white/80">规范管理</span>
            </div>
          </div>

          <!-- 品牌标语 -->
          <div class="text-white/50 text-sm italic border-l-2 border-white/30 pl-4">
            "思想的碰撞，驱动创新的未来"
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录区域 (40%) -->
    <div class="w-full lg:w-[40%] flex items-center justify-center relative z-10">
      <div class="w-full max-w-sm mx-8">
        <!-- 移动端Logo -->
        <div class="lg:hidden text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-white/90 rounded-xl mb-4 shadow-lg backdrop-blur-sm">
            <i class="fa fa-users text-blue-600 text-2xl"></i>
          </div>
          <h1 class="text-xl font-bold text-white">组会管理系统</h1>
        </div>

        <!-- 登录卡片 -->
        <div class="bg-white/85 backdrop-blur-xl rounded-3xl shadow-2xl p-8 relative overflow-hidden">
          <!-- 右上角语言选择 -->
          <div class="absolute top-4 right-4">
            <select class="bg-gray-100 text-sm text-gray-600 px-3 py-1.5 rounded-lg border-0 focus:outline-none cursor-pointer">
              <option value="zh">简体中文</option>
              <option value="en">English</option>
            </select>
          </div>

          <!-- 卡片标题 -->
          <div class="mb-8">
            <div class="text-2xl font-bold text-gray-800">欢迎登录</div>
            <div class="text-sm text-gray-500 mt-1">组会管理系统</div>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleLogin" class="space-y-5">
            <!-- 用户名 -->
            <div class="relative">
              <i class="fa fa-user absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <input type="text" v-model="username"
                     class="w-full pl-12 pr-4 py-3.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请输入用户名">
            </div>

            <!-- 密码 -->
            <div class="relative">
              <i class="fa fa-lock absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <input :type="showPassword ? 'text' : 'password'" v-model="password" @keypress.enter="handleLogin"
                     class="w-full pl-12 pr-12 py-3.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请输入密码">
              <button type="button" @click="showPassword = !showPassword"
                      class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-500 transition-colors">
                <i :class="showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"></i>
              </button>
            </div>

            <!-- 记住我 & 忘记密码 -->
            <div class="flex items-center justify-between text-sm">
              <label class="flex items-center gap-2 text-gray-600 cursor-pointer">
                <input type="checkbox" v-model="rememberMe" class="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500/30">
                <span>记住我</span>
              </label>
              <a href="#" class="text-blue-500 hover:text-blue-600 transition-colors">忘记密码?</a>
            </div>

            <!-- 登录按钮 -->
            <button type="submit" :disabled="loading"
                    class="w-full py-3.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-xl shadow-md hover:shadow-lg hover:from-blue-600 hover:to-blue-700 transition-all disabled:opacity-60 disabled:cursor-not-allowed">
              <span v-if="!loading">登录</span>
              <span v-else class="flex items-center justify-center gap-2">
                <i class="fa fa-spinner fa-spin"></i>
                <span>登录中...</span>
              </span>
            </button>
          </form>

          <!-- 其他登录方式 -->
          <div class="mt-8 pt-6 border-t border-gray-100">
            <div class="text-center text-sm text-gray-500 mb-4">其他登录方式</div>
            <div class="flex justify-center gap-8">
              <div class="flex flex-col items-center text-gray-500 hover:text-blue-500 cursor-pointer transition-colors group">
                <div class="p-3 bg-gray-100 rounded-full group-hover:bg-blue-50 transition-colors">
                  <i class="fa fa-id-card-o text-lg"></i>
                </div>
                <span class="text-xs mt-2">SSO登录</span>
              </div>
              <div class="flex flex-col items-center text-gray-500 hover:text-blue-500 cursor-pointer transition-colors group">
                <div class="p-3 bg-gray-100 rounded-full group-hover:bg-blue-50 transition-colors">
                  <i class="fa fa-qrcode text-lg"></i>
                </div>
                <span class="text-xs mt-2">扫码登录</span>
              </div>
            </div>
          </div>

          <!-- 底部山水剪影装饰 -->
          <div class="absolute bottom-0 left-0 right-0 h-16 overflow-hidden opacity-10">
            <svg viewBox="0 0 400 60" class="w-full h-full fill-gray-400">
              <path d="M0,60 L0,40 Q50,20 100,35 T200,25 T300,40 T400,30 L400,60 Z"></path>
              <path d="M0,60 L0,50 Q80,30 160,45 T280,35 T400,50 L400,60 Z"></path>
            </svg>
          </div>
        </div>

        <!-- 注册链接 -->
        <div class="mt-6 text-center text-sm">
          <span class="text-gray-400">还没有账号?</span>
          <a href="/register" class="text-blue-500 font-medium hover:text-blue-600 ml-1 transition-colors">立即注册</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import axios from 'axios'
import bgImage from '../../images/image.png'

const userStore = useUserStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)

onMounted(async () => {
  const sessionToken = localStorage.getItem('session_token')
  if (sessionToken) {
    try {
      const res = await axios.get('/api/auth/session-status', {
        headers: { Authorization: `Bearer ${sessionToken}` }
      })
      if (res.data.success && res.data.data?.authenticated) {
        window.location.href = `/?session_token=${sessionToken}`
      } else {
        localStorage.removeItem('session_token')
        localStorage.removeItem('user_info')
      }
    } catch (e) {
      localStorage.removeItem('session_token')
      localStorage.removeItem('user_info')
    }
  }
})

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
      localStorage.setItem('session_token', res.data.session_token)
      localStorage.setItem('user_info', JSON.stringify({ username: username.value.trim() }))
      userStore.setToken(res.data.session_token)

      window.$toast?.('登录成功', 'success')

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
</script>