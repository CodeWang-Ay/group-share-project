<template>
  <div class="bg-gray-50 min-h-screen flex items-center justify-center p-4">
    <!-- 注册面板 -->
    <div class="w-full max-w-md">
      <div class="bg-white rounded-xl p-8 shadow-lg shadow-gray-200/50">
        <!-- 顶部Logo与标题 -->
        <div class="flex items-center gap-3 mb-6">
          <i class="fa fa-flask text-primary text-2xl"></i>
          <h1 class="text-gray-800 text-xl font-bold">智能计算实验室</h1>
        </div>

        <!-- 注册标题 -->
        <div class="mb-6 text-center">
          <h2 class="text-2xl font-bold text-gray-800 mb-1">创建账号</h2>
          <p class="text-gray-500">填写信息完成注册，需管理员审核后激活</p>
        </div>

        <!-- 注册表单 -->
        <form @submit.prevent="handleRegister">
          <!-- 用户名 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              用户名 <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center gap-3">
              <i class="fa fa-user text-gray-400 w-5 text-center"></i>
              <input type="text" v-model="form.username"
                     :class="inputClass('username')"
                     placeholder="3-50个字符，含字母、数字、下划线" required>
            </div>
            <p v-if="errors.username" class="text-xs text-red-500 mt-1">{{ errors.username }}</p>
          </div>

          <!-- 身份角色 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              身份角色 <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center gap-3">
              <i class="fa fa-id-card-o text-gray-400 w-5 text-center"></i>
              <select v-model="form.role"
                      class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 appearance-none" required>
                <option value="">选择身份</option>
                <option value="teacher">老师</option>
                <option value="student">学生</option>
              </select>
            </div>
          </div>

          <!-- 性别 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">性别</label>
            <div class="flex items-center gap-3">
              <i class="fa fa-user text-gray-400 w-5 text-center"></i>
              <select v-model="form.gender"
                      class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 appearance-none">
                <option value="">选择性别</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </div>
          </div>

          <!-- 手机号码 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">手机号码</label>
            <div class="flex items-center gap-3">
              <i class="fa fa-phone text-gray-400 w-5 text-center"></i>
              <input type="tel" v-model="form.phone"
                     :class="inputClass('phone')"
                     placeholder="请输入手机号码">
            </div>
            <p v-if="errors.phone" class="text-xs text-red-500 mt-1">{{ errors.phone }}</p>
          </div>

          <!-- 学位类型（学生才显示） -->
          <div class="mb-5" v-if="form.role === 'student'">
            <label class="block text-sm font-medium text-gray-700 mb-1">学位类型</label>
            <div class="flex items-center gap-3">
              <i class="fa fa-graduation-cap text-gray-400 w-5 text-center"></i>
              <select v-model="form.degree_type"
                      class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 appearance-none">
                <option value="">选择学位类型</option>
                <option value="博士">博士</option>
                <option value="硕士">硕士</option>
                <option value="本科">本科</option>
              </select>
            </div>
          </div>

          <!-- 电子邮箱 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">电子邮箱</label>
            <div class="flex items-center gap-3">
              <i class="fa fa-envelope-o text-gray-400 w-5 text-center"></i>
              <input type="email" v-model="form.email"
                     :class="inputClass('email')"
                     placeholder="建议使用学校官方邮箱">
            </div>
            <p class="text-xs text-gray-500 mt-1">用于接收审核通知与重要消息</p>
            <p v-if="errors.email" class="text-xs text-red-500 mt-1">{{ errors.email }}</p>
          </div>

          <!-- 密码 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              设置密码 <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center gap-3">
              <i class="fa fa-lock text-gray-400 w-5 text-center"></i>
              <input type="password" v-model="form.password"
                     :class="inputClass('password')"
                     placeholder="至少6位，含字母和数字" required>
            </div>
            <p v-if="errors.password" class="text-xs text-red-500 mt-1">{{ errors.password }}</p>
          </div>

          <!-- 确认密码 -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              确认密码 <span class="text-red-500">*</span>
            </label>
            <div class="flex items-center gap-3">
              <i class="fa fa-lock text-gray-400 w-5 text-center"></i>
              <input type="password" v-model="form.confirmPassword"
                     :class="inputClass('confirmPassword')"
                     placeholder="再次输入密码" required>
            </div>
            <p v-if="errors.confirmPassword" class="text-xs text-red-500 mt-1">{{ errors.confirmPassword }}</p>
          </div>

          <!-- 用户协议 -->
          <div class="mb-6">
            <label class="flex items-start">
              <input type="checkbox" v-model="form.agreement" class="mt-1 text-primary focus:ring-primary/30 rounded">
              <span class="ml-2 text-sm text-gray-600">
                我已阅读并同意<a href="#" class="text-primary hover:underline">用户协议</a>
              </span>
            </label>
            <p v-if="errors.agreement" class="text-xs text-red-500 mt-1">{{ errors.agreement }}</p>
          </div>

          <!-- 提交按钮 -->
          <button type="submit" :disabled="loading"
                  class="w-full bg-primary text-white rounded-lg py-3 font-medium hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:cursor-not-allowed">
            <span v-if="!loading">注册账号</span>
            <span v-else class="flex items-center justify-center gap-2">
              <i class="fa fa-spinner fa-spin"></i>
              <span>注册中...</span>
            </span>
          </button>

          <!-- 已有账号 -->
          <div class="text-center text-sm text-gray-500 mt-4">
            <p>已有账号? <a href="/login" class="text-primary hover:text-primary/80 font-medium">立即登录</a></p>
          </div>
        </form>

        <!-- 底部提示 -->
        <div class="mt-6 pt-6 border-t border-gray-100 text-center text-xs text-gray-500">
          <p>疑问联系：<a href="mailto:admin@lab.example.com" class="text-primary hover:underline">admin@lab.example.com</a></p>
        </div>
      </div>
    </div>

    <!-- 成功提示弹窗 -->
    <div v-if="showSuccessModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-sm mx-4 text-center">
        <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="fa fa-check text-green-600 text-xl"></i>
        </div>
        <h3 class="text-lg font-semibold text-gray-800 mb-2">注册成功！</h3>
        <p class="text-sm text-gray-600 mb-4">您的账号已提交，等待管理员审核后即可登录使用</p>
        <button @click="goToLogin" class="w-full bg-primary text-white rounded-lg py-2 hover:bg-primary/90 transition-colors">
          前往登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import axios from 'axios'

const loading = ref(false)
const showSuccessModal = ref(false)

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
  email: '',
  phone: '',
  agreement: ''
})

// 输入框样式（根据验证状态）
const inputClass = (field) => {
  const base = 'w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all'
  if (errors[field]) {
    return `${base} border-red-500`
  }
  // 实时验证成功的字段显示绿色边框
  if (form[field] && !errors[field] && fieldValid[field]) {
    return `${base} border-green-500`
  }
  return base
}

// 实时验证状态
const fieldValid = reactive({
  username: false,
  password: false,
  confirmPassword: false,
  email: false,
  phone: false
})

// 实时验证用户名
const validateUsername = () => {
  const value = form.username.trim()
  if (value.length === 0) {
    errors.username = ''
    fieldValid.username = false
  } else if (value.length < 3 || value.length > 50) {
    errors.username = '用户名长度必须在3-50个字符之间'
    fieldValid.username = false
  } else if (!/^[a-zA-Z0-9_]+$/.test(value)) {
    errors.username = '用户名只能包含字母、数字和下划线'
    fieldValid.username = false
  } else {
    errors.username = ''
    fieldValid.username = true
  }
}

// 实时验证密码
const validatePassword = () => {
  const value = form.password.trim()
  if (value.length === 0) {
    errors.password = ''
    fieldValid.password = false
  } else if (value.length < 6) {
    errors.password = '密码长度至少为6位'
    fieldValid.password = false
  } else {
    errors.password = ''
    fieldValid.password = true
  }
  // 同时验证确认密码
  if (form.confirmPassword) validateConfirmPassword()
}

// 实时验证确认密码
const validateConfirmPassword = () => {
  const value = form.confirmPassword.trim()
  if (value.length === 0) {
    errors.confirmPassword = ''
    fieldValid.confirmPassword = false
  } else if (value !== form.password) {
    errors.confirmPassword = '两次输入的密码不一致'
    fieldValid.confirmPassword = false
  } else {
    errors.confirmPassword = ''
    fieldValid.confirmPassword = true
  }
}

// 实时验证邮箱
const validateEmail = () => {
  const value = form.email.trim()
  if (value.length === 0) {
    errors.email = ''
    fieldValid.email = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    errors.email = '请输入有效的电子邮箱地址'
    fieldValid.email = false
  } else {
    errors.email = ''
    fieldValid.email = true
  }
}

// 实时验证手机号
const validatePhone = () => {
  const value = form.phone.trim()
  if (value.length === 0) {
    errors.phone = ''
    fieldValid.phone = false
  } else if (!/^1[3-9]\d{9}$/.test(value)) {
    errors.phone = '请输入有效的手机号码'
    fieldValid.phone = false
  } else {
    errors.phone = ''
    fieldValid.phone = true
  }
}

// 监听输入变化进行实时验证
import { watch } from 'vue'
watch(() => form.username, validateUsername)
watch(() => form.password, validatePassword)
watch(() => form.confirmPassword, validateConfirmPassword)
watch(() => form.email, validateEmail)
watch(() => form.phone, validatePhone)

// 提交表单
async function handleRegister() {
  // 清除所有错误
  Object.keys(errors).forEach(key => errors[key] = '')

  // 基础验证
  if (!form.username.trim()) {
    errors.username = '请填写用户名'
  }
  if (!form.password.trim()) {
    errors.password = '请填写密码'
  }
  if (!form.confirmPassword.trim()) {
    errors.confirmPassword = '请确认密码'
  }
  if (!form.role) {
    window.$toast?.('请选择身份角色', 'error')
    return
  }
  if (!form.agreement) {
    errors.agreement = '请同意用户协议'
  }

  // 检查是否有错误
  const hasError = Object.values(errors).some(e => e)
  if (hasError) return

  // 重复验证（确保实时验证通过）
  validateUsername()
  validatePassword()
  validateConfirmPassword()
  if (form.email) validateEmail()
  if (form.phone) validatePhone()

  if (Object.values(errors).some(e => e)) return

  loading.value = true

  try {
    const response = await axios.post('/api/auth/register', {
      username: form.username.trim(),
      password: form.password.trim(),
      role: form.role,
      gender: form.gender,
      phone: form.phone.trim(),
      email: form.email.trim(),
      degree_type: form.degree_type
    })

    if (response.data.success) {
      showSuccessModal.value = true
    } else {
      window.$toast?.(response.data.message || '注册失败，请重试', 'error')
    }
  } catch (err) {
    const message = err.response?.data?.message || '网络错误，请检查连接后重试'
    window.$toast?.(message, 'error')
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  window.location.href = '/login'
}
</script>