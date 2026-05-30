<template>
  <div class="min-h-screen flex relative overflow-hidden">
    <!-- 全屏背景图片 -->
    <img :src="bgImage" class="fixed inset-0 w-full h-full object-cover" alt="background">
    <!-- 科技光效点缀 -->
    <div class="fixed inset-0 bg-gradient-to-r from-blue-900/40 via-transparent to-transparent"></div>
    <div class="fixed top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-purple-400 to-transparent opacity-60"></div>

    <!-- 左侧品牌区域 (50%) -->
    <div class="hidden lg:flex lg:w-1/2 relative z-10 flex-col items-center">
      <div class="flex flex-col h-full px-16 py-12 text-white">
        <!-- 顶部品牌标识 - 与登录卡片齐平 -->
        <div class="flex-1 flex items-center justify-center -mt-60 ml-[150px]">
          <div class="text-center">
            <div class="flex items-center gap-5 mb-6 justify-center">
              <div class="w-20 h-20 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <i class="fa fa-users text-5xl"></i>
              </div>
              <div>
                <div class="text-5xl font-bold tracking-wide" style="color: #1e3a5f;">组会管理系统</div>
                <div class="text-base text-white/70 tracking-[0.2em] mt-2" style="color: #1e3a5f;">GROUP MEETING MANAGEMENT SYSTEM</div>
              </div>
            </div>
            <div class="text-xl text-white/60 font-light mt-4 tracking-[0.5em]" style="color: #1e3a5f;">高效协作 · 有序管理 · 智慧组会</div>
          </div>
        </div>

        <!-- 底部功能亮点区 -->
        <div class="ml-[150px] pb-4">
          <!-- 四个功能图标 -->
          <div class="flex gap-12 mb-8">
            <div class="flex flex-col items-center">
              <div class="feature-icon w-18 h-18 bg-white/15 rounded-xl flex items-center justify-center mb-4 backdrop-blur-sm hover:bg-white/25 transition-colors cursor-pointer" style="width: 72px; height: 72px;">
                <i class="fa fa-calendar text-2xl"></i>
              </div>
              <span class="text-base text-white/80">组会计划</span>
            </div>
            <div class="flex flex-col items-center">
              <div class="feature-icon w-18 h-18 bg-white/15 rounded-xl flex items-center justify-center mb-4 backdrop-blur-sm hover:bg-white/25 transition-colors cursor-pointer" style="width: 72px; height: 72px;">
                <i class="fa fa-users text-2xl"></i>
              </div>
              <span class="text-base text-white/80">协作共享</span>
            </div>
            <div class="flex flex-col items-center">
              <div class="feature-icon w-18 h-18 bg-white/15 rounded-xl flex items-center justify-center mb-4 backdrop-blur-sm hover:bg-white/25 transition-colors cursor-pointer" style="width: 72px; height: 72px;">
                <i class="fa fa-line-chart text-2xl"></i>
              </div>
              <span class="text-base text-white/80">进度跟踪</span>
            </div>
            <div class="flex flex-col items-center">
              <div class="feature-icon w-18 h-18 bg-white/15 rounded-xl flex items-center justify-center mb-4 backdrop-blur-sm hover:bg-white/25 transition-colors cursor-pointer" style="width: 72px; height: 72px;">
                <i class="fa fa-shield text-2xl"></i>
              </div>
              <span class="text-base text-white/80">规范管理</span>
            </div>
          </div>

          <!-- 品牌标语 -->
          <div class="text-white/50 text-sm italic border-l-2 border-white/30 pl-4">
            "思想的碰撞，驱动创新的未来"
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧注册区域 (50%) -->
    <div class="w-full lg:w-1/2 flex items-center justify-center relative z-10">
      <div class="w-full max-w-md mx-8 -ml-16">
        <!-- 移动端Logo -->
        <div class="lg:hidden text-center mb-8">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-white/90 rounded-xl mb-4 shadow-lg backdrop-blur-sm">
            <i class="fa fa-users text-blue-600 text-2xl"></i>
          </div>
          <h1 class="text-xl font-bold text-white">组会管理系统</h1>
        </div>

        <!-- 注册卡片 -->
        <div class="login-card bg-white/85 backdrop-blur-xl rounded-3xl shadow-2xl p-8 pb-16 relative overflow-hidden min-h-[550px] flex flex-col">
          <!-- 右上角语言选择 -->
          <div class="absolute top-4 right-4">
            <select class="bg-gray-100 text-sm text-gray-600 px-3 py-1.5 rounded-lg border-0 focus:outline-none cursor-pointer">
              <option value="zh">简体中文</option>
              <option value="en">English</option>
            </select>
          </div>

          <!-- 卡片标题 -->
          <div class="mb-8">
            <div class="text-2xl font-bold text-gray-800">创建账号</div>
            <div class="text-sm text-gray-500 mt-1">填写信息完成注册，需管理员审核后激活</div>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleRegister" class="space-y-5">
            <!-- 用户名 -->
            <div class="relative">
              <i class="fa fa-user absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-red-500 text-xs">*必填</span>
              <input type="text" v-model="form.username"
                     class="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请输入用户名（3-50字符）">
            </div>

            <!-- 身份角色 -->
            <div class="relative">
              <i class="fa fa-id-card-o absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-red-500 text-xs">*必填</span>
              <select v-model="form.role"
                      class="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 appearance-none">
                <option value="">选择身份</option>
                <option value="teacher">老师</option>
                <option value="student">学生</option>
              </select>
            </div>

            <!-- 性别（选填） -->
            <div class="relative">
              <i class="fa fa-user absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs">选填</span>
              <div class="pl-12 flex gap-2">
                <button type="button" @click="form.gender = 'male'"
                        :class="form.gender === 'male' ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'"
                        class="py-2 px-5 rounded-lg border text-sm font-medium transition-all hover:border-blue-400">
                  <i class="fa fa-male mr-1"></i>男
                </button>
                <button type="button" @click="form.gender = 'female'"
                        :class="form.gender === 'female' ? 'bg-blue-500 text-white border-blue-500' : 'bg-gray-50 text-gray-600 border-gray-200'"
                        class="py-2 px-5 rounded-lg border text-sm font-medium transition-all hover:border-blue-400">
                  <i class="fa fa-female mr-1"></i>女
                </button>
              </div>
            </div>

            <!-- 手机号码（选填） -->
            <div class="relative">
              <i class="fa fa-phone absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs">选填</span>
              <input type="tel" v-model="form.phone"
                     class="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请输入手机号码">
            </div>

            <!-- 学位类型（学生才显示，选填） -->
            <div class="relative" v-if="form.role === 'student'">
              <i class="fa fa-graduation-cap absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs">选填</span>
              <select v-model="form.degree_type"
                      class="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 appearance-none">
                <option value="">选择学位类型</option>
                <option value="博士">博士</option>
                <option value="硕士">硕士</option>
                <option value="本科">本科</option>
              </select>
            </div>

            <!-- 电子邮箱（选填） -->
            <div class="relative">
              <i class="fa fa-envelope-o absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-xs">选填</span>
              <input type="email" v-model="form.email"
                     class="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请输入邮箱（建议使用学校邮箱）">
            </div>

            <!-- 密码 -->
            <div class="relative">
              <i class="fa fa-lock absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-16 top-1/2 -translate-y-1/2 text-red-500 text-xs">*必填</span>
              <input :type="showPassword ? 'text' : 'password'" v-model="form.password"
                     class="w-full pl-12 pr-16 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请输入密码（至少6位）">
              <button type="button" @click="showPassword = !showPassword"
                      class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-blue-500 transition-colors">
                <i :class="showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"></i>
              </button>
            </div>

            <!-- 确认密码 -->
            <div class="relative">
              <i class="fa fa-lock absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <span class="absolute right-4 top-1/2 -translate-y-1/2 text-red-500 text-xs">*必填</span>
              <input type="password" v-model="form.confirmPassword"
                     class="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                     placeholder="请确认密码">
            </div>

            <!-- 用户协议 -->
            <div class="flex items-center gap-2 text-sm">
              <input type="checkbox" v-model="form.agreement" class="w-4 h-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500/30">
              <span class="text-gray-600">我已阅读并同意<a href="#" class="text-blue-500 hover:underline">用户协议</a></span>
            </div>

            <!-- 注册按钮 -->
            <button type="submit" :disabled="loading"
                    class="w-full py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-xl shadow-md hover:shadow-lg hover:from-blue-600 hover:to-blue-700 transition-all disabled:opacity-60 disabled:cursor-not-allowed">
              <span v-if="!loading">注册账号</span>
              <span v-else class="flex items-center justify-center gap-2">
                <i class="fa fa-spinner fa-spin"></i>
                <span>注册中...</span>
              </span>
            </button>
          </form>

          <!-- 登录链接 -->
        <div class="mt-6 text-center text-sm">
          <span class="text-gray-400">已有账号?</span>
          <button type="button" @click="goToLogin" class="text-blue-500 font-medium hover:text-blue-600 ml-1 transition-colors cursor-pointer underline">立即登录</button>
        </div>

          <!-- 底部山水剪影装饰 -->
          <div class="absolute bottom-0 left-0 right-0 h-16 overflow-hidden opacity-10 pointer-events-none">
            <svg viewBox="0 0 400 60" class="w-full h-full fill-gray-400">
              <path d="M0,60 L0,40 Q50,20 100,35 T200,25 T300,40 T400,30 L400,60 Z"></path>
              <path d="M0,60 L0,50 Q80,30 160,45 T280,35 T400,50 L400,60 Z"></path>
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- 成功提示弹窗 -->
    <div v-if="showSuccessModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-2xl p-8 max-w-sm mx-4 text-center shadow-xl">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="fa fa-check text-green-600 text-2xl"></i>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-2">注册成功！</h3>
        <p class="text-sm text-gray-600 mb-6">您的账号已提交，等待管理员审核后即可登录使用</p>
        <button @click="goToLogin" class="w-full py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all">
          前往登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import axios from 'axios'
import bgImage from '../../images/Common.png'

const loading = ref(false)
const showSuccessModal = ref(false)
const showPassword = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  role: '',
  gender: '',
  phone: '',
  email: '',
  degree_type: '',
  agreement: false
})

const errors = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: ''
})

// 实时验证
watch(() => form.username, (val) => {
  const v = val.trim()
  errors.username = v.length > 0 && (v.length < 3 || v.length > 50 || !/^[a-zA-Z0-9_]+$/.test(v))
    ? '用户名需要3-50个字符，只含字母数字下划线' : ''
})

watch(() => form.password, (val) => {
  const v = val.trim()
  errors.password = v.length > 0 && v.length < 6 ? '密码至少6位' : ''
  if (form.confirmPassword) {
    errors.confirmPassword = form.confirmPassword !== val ? '密码不一致' : ''
  }
})

watch(() => form.confirmPassword, (val) => {
  errors.confirmPassword = val && val !== form.password ? '密码不一致' : ''
})

watch(() => form.email, (val) => {
  const v = val.trim()
  errors.email = v.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? '邮箱格式不正确' : ''
})

// 提交表单
async function handleRegister() {
  if (!form.username.trim()) {
    window.$toast?.('请输入用户名', 'error')
    return
  }
  if (!form.password.trim()) {
    window.$toast?.('请输入密码', 'error')
    return
  }
  if (!form.confirmPassword.trim()) {
    window.$toast?.('请确认密码', 'error')
    return
  }
  if (form.password !== form.confirmPassword) {
    window.$toast?.('两次密码不一致', 'error')
    return
  }
  if (!form.role) {
    window.$toast?.('请选择身份', 'error')
    return
  }
  if (!form.agreement) {
    window.$toast?.('请同意用户协议', 'error')
    return
  }

  loading.value = true

  try {
    const res = await axios.post('/api/auth/register', {
      username: form.username.trim(),
      password: form.password.trim(),
      role: form.role,
      gender: form.gender,
      phone: form.phone.trim(),
      email: form.email.trim(),
      degree_type: form.degree_type
    })

    if (res.data.success) {
      showSuccessModal.value = true
    } else {
      window.$toast?.(res.data.message || '注册失败', 'error')
    }
  } catch (e) {
    const message = e.response?.data?.message || '网络错误，请稍后重试'
    window.$toast?.(message, 'error')
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  console.log('=== goToLogin 点击触发 ===')
  console.log('当前路径:', window.location.pathname)
  window.location.href = '/login'
  console.log('=== 正在跳转到 /login ===')
}
</script>

<style scoped>
/* 页面加载动画 */
.login-card {
  animation: fadeInUp 0.8s ease-out;
}

.login-card > * {
  animation: fadeIn 0.6s ease-out forwards;
  opacity: 0;
}

.login-card > *:nth-child(1) { animation-delay: 0.1s; }
.login-card > *:nth-child(2) { animation-delay: 0.2s; }
.login-card > *:nth-child(3) { animation-delay: 0.3s; }

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 功能图标悬浮动画 */
.feature-icon {
  transition: all 0.3s ease;
}

.feature-icon:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(255, 255, 255, 0.2);
}
</style>