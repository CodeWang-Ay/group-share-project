<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <!-- 页面标题 -->
    <div class="mb-6 flex flex-wrap justify-between items-center gap-4">
      <div>
        <h1 class="text-2xl font-bold">编辑个人资料</h1>
        <p class="text-gray-500">更新您的个人信息和偏好设置</p>
      </div>
      <div class="flex items-center gap-3">
        <router-link to="/" class="border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2">
          <i class="fa fa-arrow-left"></i>
          <span>返回</span>
        </router-link>
        <button @click="saveProfile" :disabled="saving" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2 disabled:opacity-50">
          <i class="fa fa-save"></i>
          <span>{{ saving ? '保存中...' : '保存修改' }}</span>
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="bg-white rounded-lg shadow-sm border p-6 text-center">
      <i class="fa fa-spinner fa-spin text-2xl text-gray-400"></i>
      <p class="text-gray-500 mt-2">加载中...</p>
    </div>

    <!-- 个人资料表单 -->
    <div v-else class="bg-white rounded-lg shadow-sm border p-6">
      <!-- 基本信息 -->
      <div class="py-6 border-b border-gray-100">
        <h2 class="text-lg font-bold mb-5">基本信息</h2>
        <div class="flex flex-col sm:flex-row gap-6">
          <!-- 头像区域 -->
          <div class="flex flex-col items-center sm:items-start">
            <div class="relative mb-3">
              <img :src="avatarUrl" alt="个人头像" class="w-32 h-32 rounded-full object-cover border-4 border-white shadow-sm">
              <div @click="triggerAvatarUpload" class="absolute inset-0 bg-black/40 rounded-full opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer">
                <i class="fa fa-camera text-white text-xl"></i>
              </div>
              <input ref="avatarInput" type="file" accept="image/*" @change="handleAvatarChange" class="hidden">
            </div>
            <button @click="triggerAvatarUpload" class="text-sm text-primary hover:text-primary/80 flex items-center">
              <i class="fa fa-upload mr-1"></i> 更换头像
            </button>
            <p class="text-xs text-gray-500 mt-1">支持JPG、PNG格式，建议尺寸200×200px</p>
          </div>

          <!-- 基本信息表单 -->
          <div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">用户名/姓名 <span class="text-red-500">*</span></label>
              <input v-model="profile.username" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" required>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">性别 <span class="text-red-500">*</span></label>
              <select v-model="profile.gender" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" required>
                <option value="" disabled>请选择性别</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">身份角色</label>
              <input :value="roleText" type="text" class="w-full bg-gray-100 border border-gray-200 rounded-lg px-4 py-2.5 text-sm text-gray-500 cursor-not-allowed" disabled>
              <p class="text-xs text-gray-500 mt-1">角色由管理员分配，不可自行修改</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">学号/工号 <span class="text-red-500">*</span></label>
              <input v-model="profile.student_id" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" required>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">创建时间</label>
              <input :value="profile.created_at" type="text" class="w-full bg-gray-100 border border-gray-200 rounded-lg px-4 py-2.5 text-sm text-gray-500 cursor-not-allowed" disabled>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">更新时间</label>
              <input :value="profile.updated_at" type="text" class="w-full bg-gray-100 border border-gray-200 rounded-lg px-4 py-2.5 text-sm text-gray-500 cursor-not-allowed" disabled>
            </div>
          </div>
        </div>
      </div>

      <!-- 联系信息 -->
      <div class="py-6 border-b border-gray-100">
        <h2 class="text-lg font-bold mb-5">联系信息</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">电子邮箱 <span class="text-red-500">*</span></label>
            <input v-model="profile.email" type="email" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" required>
            <p class="text-xs text-gray-500 mt-1">用于接收系统通知和重置密码</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">电话号码</label>
            <input v-model="profile.phone" type="tel" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">个人主页</label>
            <input v-model="profile.personal_homepage" type="url" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="https://...">
            <p class="text-xs text-gray-500 mt-1">个人学术主页或GitHub等链接</p>
          </div>
        </div>
      </div>

      <!-- 身份信息 -->
      <div class="py-6 border-b border-gray-100">
        <h2 class="text-lg font-bold mb-5">身份信息</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">身份证号</label>
            <input v-model="profile.id_card" type="text" maxlength="18" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="18位身份证号码">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">银行卡号</label>
            <input v-model="profile.bank_card" type="text" maxlength="19" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" placeholder="16-19位银行卡号">
          </div>
        </div>
      </div>

      <!-- 学业/职业信息 -->
      <div class="py-6 border-b border-gray-100">
        <h2 class="text-lg font-bold mb-5">学业/职业信息</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">毕业状态</label>
            <select v-model="profile.graduation_status" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
              <option value="在读">在读</option>
              <option value="已毕业">已毕业</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">导师姓名</label>
            <input v-model="profile.supervisor" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">学位类型</label>
            <select v-model="profile.degree_type" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
              <option value="">请选择学位类型</option>
              <option value="本科">本科</option>
              <option value="硕士">硕士</option>
              <option value="博士">博士</option>
              <option value="博士后">博士后</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">研究方向 <span class="text-red-500">*</span></label>
            <input v-model="profile.research_direction" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30" required>
            <p class="text-xs text-gray-500 mt-1">请用逗号分隔多个研究方向</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">工作地点</label>
            <input v-model="profile.work_location" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">工作公司</label>
            <input v-model="profile.work_company" type="text" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
            <p class="text-xs text-gray-500 mt-1">学生可留空，教职工或已毕业学生请填写</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">状态</label>
            <select v-model="profile.status" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30">
              <option value="active">正常</option>
              <option value="leave">休假</option>
              <option value="sabbatical">学术休假</option>
              <option value="other">其他</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 个人简介 -->
      <div class="py-6 border-b border-gray-100">
        <h2 class="text-lg font-bold mb-5">个人简介</h2>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1.5">个人简介</label>
          <textarea v-model="profile.personal_bio" rows="4" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none" placeholder="简要介绍您的教育背景、研究兴趣等"></textarea>
          <p class="text-xs text-gray-500 mt-1">最多500字</p>
        </div>
      </div>

      <!-- 隐私设置 -->
      <div class="py-6">
        <h2 class="text-lg font-bold mb-5">隐私设置</h2>
        <div class="space-y-4">
          <div class="flex items-start gap-3">
            <label class="relative inline-flex items-center cursor-pointer mt-1">
              <input v-model="profile.show_contact" type="checkbox" class="sr-only peer">
              <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
            </label>
            <div>
              <h3 class="font-medium text-sm">允许其他成员查看我的联系方式</h3>
              <p class="text-xs text-gray-500 mt-0.5">开启后，实验室其他成员可以查看您的邮箱和电话</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <label class="relative inline-flex items-center cursor-pointer mt-1">
              <input v-model="profile.receive_reminder" type="checkbox" class="sr-only peer">
              <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary"></div>
            </label>
            <div>
              <h3 class="font-medium text-sm">接收组会提醒通知</h3>
              <p class="text-xs text-gray-500 mt-0.5">组会开始前通过邮件和系统消息提醒您</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { profileApi } from '../api/profile'
import { getAvatarUrl, SERVER_URL } from '../config'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const saving = ref(false)
const avatarInput = ref(null)

const profile = ref({
  username: '',
  gender: '',
  role: '',
  student_id: '',
  email: '',
  phone: '',
  personal_homepage: '',
  id_card: '',
  bank_card: '',
  graduation_status: '在读',
  supervisor: '',
  degree_type: '',
  research_direction: '',
  work_location: '',
  work_company: '',
  status: 'active',
  personal_bio: '',
  created_at: '',
  updated_at: '',
  avatar: '',
  show_contact: true,
  receive_reminder: true
})

const roleText = computed(() => {
  const roles = { admin: '管理员', teacher: '导师', student: '学生' }
  return roles[profile.value.role] || '未知'
})

const avatarUrl = computed(() => {
  if (profile.value.avatar) {
    if (profile.value.avatar.startsWith('/uploads')) {
      return `${SERVER_URL}${profile.value.avatar}`
    }
    return profile.value.avatar
  }
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.value.username || 'User')}&background=2563eb&color=fff&size=200`
})

async function loadProfile() {
  loading.value = true
  try {
    const res = await profileApi.getProfile()
    if (res.data.success) {
      const data = res.data.data
      profile.value = {
        ...profile.value,
        ...data,
        show_contact: data.show_contact ?? true,
        receive_reminder: data.receive_reminder ?? true
      }
      // 同步更新 userStore
      if (data.username) {
        userStore.setUserInfo({
          id: data.id,
          username: data.username,
          role: data.role,
          avatar: data.avatar
        })
      }
    }
  } catch (e) {
    console.error('加载个人资料失败:', e)
    window.$toast?.('加载个人资料失败', 'error')
  }
  loading.value = false
}

async function saveProfile() {
  saving.value = true
  try {
    const res = await profileApi.updateProfile(profile.value)
    if (res.data.success) {
      window.$toast?.('个人资料已更新', 'success')
      // 同步更新 userStore
      userStore.setUserInfo({
        id: profile.value.id,
        username: profile.value.username,
        role: profile.value.role,
        avatar: profile.value.avatar
      })
      loadProfile()
    } else {
      window.$toast?.(res.data.message || '保存失败', 'error')
    }
  } catch (e) {
    console.error('保存个人资料失败:', e)
    window.$toast?.('保存失败，请重试', 'error')
  }
  saving.value = false
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

async function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return

  // 检查文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    window.$toast?.('只支持 JPG、PNG、GIF、WEBP 格式', 'error')
    return
  }

  // 检查文件大小
  if (file.size > 5 * 1024 * 1024) {
    window.$toast?.('图片大小不能超过 5MB', 'error')
    return
  }

  // 本地预览
  const reader = new FileReader()
  reader.onload = (e) => {
    profile.value.avatar = e.target.result
  }
  reader.readAsDataURL(file)

  // 上传到服务器
  try {
    const res = await profileApi.uploadAvatar(file)
    if (res.data.success) {
      profile.value.avatar = res.data.data.avatar_url
      userStore.setUserInfo({
        ...userStore.userInfo,
        avatar: res.data.data.avatar_url
      })
      window.$toast?.('头像上传成功', 'success')
    } else {
      window.$toast?.(res.data.message || '上传失败', 'error')
    }
  } catch (e) {
    console.error('上传头像失败:', e)
    window.$toast?.('上传失败，请重试', 'error')
  }
}

onMounted(loadProfile)
</script>