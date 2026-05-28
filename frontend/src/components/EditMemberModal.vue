<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col overflow-hidden">
      <div class="p-4 border-b flex-shrink-0 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-800">编辑成员信息</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><i class="fa fa-times text-xl"></i></button>
      </div>
      <div class="p-6 flex-1 overflow-y-auto">
        <form class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">姓名 *</label>
              <input v-model="form.username" type="text" required class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">学号/工号 *</label>
              <input v-model="form.student_id" type="text" required class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">身份证号</label>
              <input v-model="form.id_card" type="text" maxlength="18" placeholder="18位身份证号" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">银行卡号</label>
              <input v-model="form.bank_card" type="text" placeholder="银行卡号" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">邮箱 *</label>
              <input v-model="form.email" type="email" required class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">手机号</label>
              <input v-model="form.phone" type="tel" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">角色 *</label>
              <select v-model="form.role" required class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="">请选择角色</option>
                <option value="student">学生</option>
                <option value="teacher">导师</option>
                <option value="admin">管理员</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">状态</label>
              <select v-model="form.status" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="active">激活</option>
                <option value="inactive">停用</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">学位类型</label>
              <select v-model="form.degree_type" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="">请选择学位类型</option>
                <option value="博士">博士</option>
                <option value="硕士">硕士</option>
                <option value="本科">本科</option>
                <option value="博士后">博士后</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">性别</label>
              <select v-model="form.gender" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="">请选择性别</option>
                <option value="male">男</option>
                <option value="female">女</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">研究方向</label>
              <input v-model="form.research_direction" type="text" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">个人简介</label>
              <input v-model="form.personal_bio" type="text" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
          </div>
        </form>
      </div>
      <div class="p-4 border-t flex justify-between gap-3 flex-shrink-0 bg-white">
        <div class="flex gap-3">
          <button v-if="isAdmin" @click="$emit('reset-password', member)" class="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 flex items-center gap-2">
            <i class="fa fa-key"></i>重置密码
          </button>
        </div>
        <div class="flex gap-3">
          <button @click="$emit('close')" class="px-4 py-2 border rounded-lg hover:bg-gray-100">取消</button>
          <button @click="submitForm" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90" :disabled="saving">
            <i v-if="saving" class="fa fa-spinner fa-spin mr-1"></i>保存更改
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  member: Object,
  isAdmin: Boolean
})

const emit = defineEmits(['close', 'save', 'reset-password'])

const form = ref({
  username: '',
  student_id: '',
  email: '',
  phone: '',
  role: '',
  status: 'active',
  degree_type: '',
  gender: '',
  research_direction: '',
  personal_bio: '',
  id_card: '',
  bank_card: ''
})

const saving = ref(false)

watch(() => props.member, (m) => {
  if (m) {
    form.value = {
      username: m.username || '',
      student_id: m.student_id || '',
      email: m.email || '',
      phone: m.phone || '',
      role: m.role || '',
      status: m.status || 'active',
      degree_type: m.degree_type || '',
      gender: m.gender || '',
      research_direction: m.research_direction || '',
      personal_bio: m.personal_bio || '',
      id_card: m.id_card || '',
      bank_card: m.bank_card || ''
    }
  }
}, { immediate: true })

function submitForm() {
  if (!form.value.username || !form.value.student_id || !form.value.email || !form.value.role) {
    window.$toast?.('请填写必填字段', 'error')
    return
  }
  emit('save', { ...form.value })
}
</script>