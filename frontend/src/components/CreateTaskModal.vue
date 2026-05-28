<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-xl w-full max-w-lg mx-4 p-6 relative">
      <button @click="close" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
        <i class="fa fa-times"></i>
      </button>
      <h3 class="text-lg font-semibold mb-4">新建任务</h3>
      <form @submit.prevent="submitForm" class="space-y-4">
        <div>
          <label class="block text-sm text-gray-600 mb-1">任务标题 <span class="text-red-500">*</span></label>
          <input v-model="form.title" type="text" class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/30 focus:border-primary" placeholder="输入任务标题" required>
        </div>
        <div>
          <label class="block text-sm text-gray-600 mb-1">任务描述</label>
          <textarea v-model="form.description" rows="3" class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/30 focus:border-primary" placeholder="输入任务描述"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">优先级</label>
            <select v-model="form.priority" class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="high">高优先级</option>
              <option value="middle" selected>中优先级</option>
              <option value="low">低优先级</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">截止日期</label>
            <input v-model="form.deadline" type="date" class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/30 focus:border-primary">
          </div>
        </div>
        <!-- 导师可选择负责人 -->
        <div v-if="userRole === 'teacher' || userRole === 'admin'">
          <label class="block text-sm text-gray-600 mb-1">负责人</label>
          <select v-model="form.assignee_id" class="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="">选择负责人</option>
            <option v-for="member in members" :key="member.id" :value="member.id">{{ member.username }}</option>
          </select>
        </div>
      </form>
      <div class="mt-6 flex justify-end gap-3">
        <button @click="close" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">取消</button>
        <button @click="submitForm" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">创建</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  userRole: String,
  members: Array
})

const emit = defineEmits(['submit', 'close'])

const visible = defineModel()

const form = ref({
  title: '',
  description: '',
  priority: 'middle',
  deadline: '',
  assignee_id: ''
})

// 监听visible变化，重置表单
watch(visible, (val) => {
  if (val) {
    form.value = {
      title: '',
      description: '',
      priority: 'middle',
      deadline: '',
      assignee_id: ''
    }
  }
})

const close = () => {
  visible.value = false
  emit('close')
}

const submitForm = () => {
  if (!form.value.title.trim()) {
    alert('请输入任务标题')
    return
  }

  const data = {
    title: form.value.title.trim(),
    description: form.value.description.trim(),
    priority: form.value.priority,
    deadline: form.value.deadline || null
  }

  // 如果导师选择了负责人
  if (form.value.assignee_id && (props.userRole === 'teacher' || props.userRole === 'admin')) {
    data.assignee_id = parseInt(form.value.assignee_id)
    data.task_type = 'assigned'
  }

  emit('submit', data)
}
</script>