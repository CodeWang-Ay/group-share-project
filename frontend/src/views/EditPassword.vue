<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold">修改密码</h1>
      <p class="text-gray-500">为了账户安全，请定期更换密码</p>
    </div>

    <!-- 修改密码表单 -->
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-sm border p-6 mb-6">
      <!-- 安全提示 -->
      <div class="bg-blue-50 border-l-4 border-primary p-4 mb-6 rounded-r-lg">
        <div class="flex">
          <div class="flex-shrink-0">
            <i class="fa fa-info-circle text-primary"></i>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-primary">密码安全提示</h3>
            <div class="mt-2 text-sm text-blue-700 space-y-1">
              <p>• 密码长度至少8个字符</p>
              <p>• 包含大小写字母、数字和特殊符号</p>
              <p>• 不要使用与账户名相同或容易猜测的密码</p>
              <p>• 不要与其他网站使用相同的密码</p>
            </div>
          </div>
        </div>
      </div>

      <form @submit.prevent="handleSubmit">
        <!-- 旧密码 -->
        <div class="mb-5">
          <label class="block text-sm font-medium text-gray-700 mb-1.5">当前密码 <span class="text-red-500">*</span></label>
          <div class="relative">
            <input v-model="oldPassword" :type="showOldPassword ? 'text' : 'password'"
                   class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 pr-10"
                   :class="{ 'border-red-500': errors.oldPassword }" required>
            <button type="button" @click="showOldPassword = !showOldPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <i :class="showOldPassword ? 'fa fa-eye' : 'fa fa-eye-slash'"></i>
            </button>
          </div>
          <p v-if="errors.oldPassword" class="text-xs text-red-500 mt-1">{{ errors.oldPassword }}</p>
        </div>

        <!-- 新密码 -->
        <div class="mb-5">
          <label class="block text-sm font-medium text-gray-700 mb-1.5">新密码 <span class="text-red-500">*</span></label>
          <div class="relative">
            <input v-model="newPassword" :type="showNewPassword ? 'text' : 'password'"
                   @input="checkPasswordStrength"
                   class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 pr-10"
                   :class="{ 'border-red-500': errors.newPassword }" required>
            <button type="button" @click="showNewPassword = !showNewPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <i :class="showNewPassword ? 'fa fa-eye' : 'fa fa-eye-slash'"></i>
            </button>
          </div>
          <p v-if="errors.newPassword" class="text-xs text-red-500 mt-1">{{ errors.newPassword }}</p>

          <!-- 密码强度指示器 -->
          <div class="mt-2">
            <div class="flex justify-between mb-1">
              <span class="text-xs text-gray-500">密码强度</span>
              <span class="text-xs font-medium" :class="strengthColor">{{ strengthText }}</span>
            </div>
            <div class="flex gap-1">
              <div v-for="i in 4" :key="i" class="h-1.5 w-1/4 rounded-full transition-all duration-300"
                   :class="i <= strengthLevel ? strengthBarColor : 'bg-gray-200'"></div>
            </div>
          </div>

          <!-- 密码要求提示 -->
          <div class="mt-2 space-y-1">
            <p class="text-xs flex items-center" :class="requirements.length ? 'text-green-600' : 'text-gray-500'">
              <i :class="requirements.length ? 'fa fa-check text-green-600' : 'fa fa-circle-o text-gray-400'" class="mr-2"></i>
              <span>至少8个字符</span>
            </p>
            <p class="text-xs flex items-center" :class="requirements.uppercase ? 'text-green-600' : 'text-gray-500'">
              <i :class="requirements.uppercase ? 'fa fa-check text-green-600' : 'fa fa-circle-o text-gray-400'" class="mr-2"></i>
              <span>包含至少一个大写字母</span>
            </p>
            <p class="text-xs flex items-center" :class="requirements.lowercase ? 'text-green-600' : 'text-gray-500'">
              <i :class="requirements.lowercase ? 'fa fa-check text-green-600' : 'fa fa-circle-o text-gray-400'" class="mr-2"></i>
              <span>包含至少一个小写字母</span>
            </p>
            <p class="text-xs flex items-center" :class="requirements.number ? 'text-green-600' : 'text-gray-500'">
              <i :class="requirements.number ? 'fa fa-check text-green-600' : 'fa fa-circle-o text-gray-400'" class="mr-2"></i>
              <span>包含至少一个数字</span>
            </p>
            <p class="text-xs flex items-center" :class="requirements.special ? 'text-green-600' : 'text-gray-500'">
              <i :class="requirements.special ? 'fa fa-check text-green-600' : 'fa fa-circle-o text-gray-400'" class="mr-2"></i>
              <span>包含至少一个特殊符号(!@#$%^&*等)</span>
            </p>
          </div>
        </div>

        <!-- 确认新密码 -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-1.5">确认新密码 <span class="text-red-500">*</span></label>
          <div class="relative">
            <input v-model="confirmPassword" :type="showConfirmPassword ? 'text' : 'password'"
                   @input="checkPasswordMatch"
                   class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 pr-10"
                   :class="passwordMatchStatus === 'match' ? 'border-green-500' : passwordMatchStatus === 'mismatch' ? 'border-red-500' : ''" required>
            <button type="button" @click="showConfirmPassword = !showConfirmPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <i :class="showConfirmPassword ? 'fa fa-eye' : 'fa fa-eye-slash'"></i>
            </button>
          </div>
          <p class="text-xs mt-1" :class="passwordMatchStatus === 'match' ? 'text-green-600' : passwordMatchStatus === 'mismatch' ? 'text-red-500' : 'text-gray-500'">
            {{ passwordMatchHint }}
          </p>
        </div>

        <!-- 操作按钮 -->
        <div class="flex flex-wrap gap-3">
          <router-link to="/user-profile" class="px-5 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm flex items-center gap-2">
            <i class="fa fa-arrow-left"></i>
            <span>返回个人中心</span>
          </router-link>
          <button type="submit" :disabled="submitting"
                  class="px-5 py-2.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm flex items-center gap-2 disabled:opacity-50">
            <i :class="submitting ? 'fa fa-spinner fa-spin' : 'fa fa-save'"></i>
            <span>{{ submitting ? '修改中...' : '确认修改' }}</span>
          </button>
        </div>
      </form>
    </div>

    <!-- 安全建议 -->
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-sm border p-6">
      <h2 class="text-lg font-bold mb-4">安全建议</h2>
      <ul class="space-y-3 text-sm">
        <li class="flex items-start gap-3">
          <i class="fa fa-shield text-primary mt-0.5"></i>
          <span>建议每90天更换一次密码，以保障账户安全</span>
        </li>
        <li class="flex items-start gap-3">
          <i class="fa fa-random text-primary mt-0.5"></i>
          <span>不要使用连续数字、重复字符或常见词语作为密码</span>
        </li>
        <li class="flex items-start gap-3">
          <i class="fa fa-ban text-primary mt-0.5"></i>
          <span>不要将密码告诉他人，包括实验室管理员</span>
        </li>
        <li class="flex items-start gap-3">
          <i class="fa fa-mobile text-primary mt-0.5 text-lg"></i>
          <span>如果收到可疑的密码重置通知，请及时联系管理员核实</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { passwordApi } from '../api/password'
import { getLoginUrl } from '../config'

const router = useRouter()
const userStore = useUserStore()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const showOldPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

const submitting = ref(false)
const errors = ref({})

const requirements = ref({
  length: false,
  uppercase: false,
  lowercase: false,
  number: false,
  special: false
})

const strengthLevel = ref(0)
const passwordMatchStatus = ref('') // '', 'match', 'mismatch'

const strengthText = computed(() => {
  const texts = ['未输入', '极弱', '弱', '中', '强']
  return texts[strengthLevel.value]
})

const strengthColor = computed(() => {
  const colors = ['text-gray-500', 'text-red-500', 'text-yellow-500', 'text-blue-500', 'text-green-600']
  return colors[strengthLevel.value]
})

const strengthBarColor = computed(() => {
  const colors = ['bg-gray-200', 'bg-red-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-600']
  return colors[strengthLevel.value]
})

const passwordMatchHint = computed(() => {
  if (!confirmPassword.value) return '请再次输入新密码进行确认'
  if (passwordMatchStatus.value === 'match') return '密码一致'
  if (passwordMatchStatus.value === 'mismatch') return '两次输入的密码不一致'
  return '请再次输入新密码进行确认'
})

function checkPasswordStrength() {
  const pwd = newPassword.value

  // 检查各项要求
  requirements.value.length = pwd.length >= 8
  requirements.value.uppercase = /[A-Z]/.test(pwd)
  requirements.value.lowercase = /[a-z]/.test(pwd)
  requirements.value.number = /[0-9]/.test(pwd)
  requirements.value.special = /[^A-Za-z0-9]/.test(pwd)

  // 计算强度等级
  if (!pwd) {
    strengthLevel.value = 0
    return
  }

  let score = 0
  if (pwd.length >= 8) score += 1
  if (pwd.length >= 12) score += 1
  if (requirements.value.uppercase) score += 1
  if (requirements.value.lowercase) score += 1
  if (requirements.value.number) score += 1
  if (requirements.value.special) score += 1

  strengthLevel.value = Math.min(Math.floor(score / 1.5), 4)

  // 检查密码匹配
  checkPasswordMatch()
}

function checkPasswordMatch() {
  if (!confirmPassword.value) {
    passwordMatchStatus.value = ''
    return
  }
  passwordMatchStatus.value = newPassword.value === confirmPassword.value ? 'match' : 'mismatch'
}

function validate() {
  errors.value = {}

  if (!oldPassword.value.trim()) {
    errors.value.oldPassword = '请输入当前密码'
  }

  if (!newPassword.value.trim()) {
    errors.value.newPassword = '请输入新密码'
  } else if (newPassword.value.length < 8) {
    errors.value.newPassword = '密码长度至少8个字符'
  } else if (newPassword.value === oldPassword.value) {
    errors.value.newPassword = '新密码不能与当前密码相同'
  }

  if (!confirmPassword.value.trim()) {
    errors.value.confirmPassword = '请确认新密码'
  } else if (newPassword.value !== confirmPassword.value) {
    errors.value.confirmPassword = '两次输入的密码不一致'
  }

  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  submitting.value = true
  try {
    const res = await passwordApi.changePassword(
      oldPassword.value,
      newPassword.value,
      confirmPassword.value
    )

    if (res.data.success) {
      window.$toast?.('密码修改成功，请使用新密码登录', 'success')

      // 清除登录状态
      userStore.clear()

      // 延迟跳转到登录页
      setTimeout(() => {
        window.location.href = getLoginUrl()
      }, 2000)
    } else {
      window.$toast?.(res.data.message || '修改失败', 'error')
    }
  } catch (e) {
    console.error('修改密码失败:', e)
    window.$toast?.('网络错误，请重试', 'error')
  }
  submitting.value = false
}
</script>