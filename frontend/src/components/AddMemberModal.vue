<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col overflow-hidden">
      <div class="p-4 border-b flex-shrink-0 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-800">添加新成员</h3>
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
              <label class="block text-sm font-medium text-gray-700 mb-2">密码 *</label>
              <input v-model="form.password" type="text" required placeholder="至少6位" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
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
                <option value="student">学生</option>
                <option value="teacher">导师</option>
                <option value="admin">管理员</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">学号/工号</label>
              <input v-model="form.student_id" type="text" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            </div>
          </div>
        </form>
      </div>
      <div class="p-4 border-t flex justify-end gap-3 flex-shrink-0 bg-white">
        <button @click="$emit('close')" class="px-4 py-2 border rounded-lg hover:bg-gray-100">取消</button>
        <button @click="submitForm" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90" :disabled="saving">
          <i v-if="saving" class="fa fa-spinner fa-spin mr-1"></i>添加成员
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close', 'save'])

const form = ref({
  username: '',
  password: '',
  email: '',
  phone: '',
  role: 'student',
  student_id: ''
})

const saving = ref(false)

function submitForm() {
  if (!form.value.username || !form.value.password || !form.value.email || !form.value.role) {
    window.$toast?.('请填写必填字段', 'error')
    return
  }
  if (form.value.password.length < 6) {
    window.$toast?.('密码长度至少6位', 'error')
    return
  }
  emit('save', { ...form.value })
}
</script>