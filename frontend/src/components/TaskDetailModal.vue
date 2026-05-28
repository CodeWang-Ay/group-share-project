<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-xl w-full max-w-lg mx-4 p-6 relative">
      <button @click="close" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
        <i class="fa fa-times"></i>
      </button>
      <h3 class="text-lg font-semibold mb-4">{{ task?.title || '任务详情' }}</h3>
      <div class="space-y-4">
        <div class="flex items-start gap-3">
          <label class="text-gray-500 w-20 shrink-0">描述:</label>
          <p class="text-gray-800">{{ task?.description || '无描述' }}</p>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">优先级:</label>
          <span :class="priorityClass">{{ task?.priority_text || '-' }}</span>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">状态:</label>
          <span :class="statusClass">{{ task?.status_text || '-' }}</span>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">进度:</label>
          <div class="flex-1">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>{{ task?.progress || 0 }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-primary h-2 rounded-full transition-all" :style="{ width: (task?.progress || 0) + '%' }"></div>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">负责人:</label>
          <span>{{ task?.assignee?.username || '未知' }}</span>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">创建者:</label>
          <span>{{ task?.creator?.username || '未知' }}</span>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">截止日期:</label>
          <span>{{ formatDeadline(task?.deadline) }}</span>
        </div>
        <div class="flex items-center gap-3">
          <label class="text-gray-500 w-20 shrink-0">任务类型:</label>
          <span>{{ task?.task_type === 'assigned' ? '导师分配' : '个人任务' }}</span>
        </div>
      </div>
      <div class="mt-6 flex justify-end gap-3">
        <button @click="close" class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">关闭</button>
        <button @click="edit" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">编辑</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  task: Object
})

const emit = defineEmits(['close', 'edit'])

const visible = defineModel()

const close = () => {
  visible.value = false
  emit('close')
}

const edit = () => {
  emit('edit')
}

const priorityClass = computed(() => {
  if (!props.task) return ''
  if (props.task.priority === 'high') return 'priority-high'
  if (props.task.priority === 'low') return 'priority-low'
  return 'priority-middle'
})

const statusClass = computed(() => {
  if (!props.task) return ''
  if (props.task.display_status === 'overdue') return 'status-overdue'
  if (props.task.display_status === 'ongoing') return 'status-doing'
  if (props.task.display_status === 'completed') return 'status-finish'
  return 'status-wait'
})

const formatDeadline = (deadline) => {
  if (!deadline) return '无截止日期'
  return new Date(deadline).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.priority-high {
  background-color: #fee2e2;
  color: #dc2626;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
.priority-middle {
  background-color: #fef3c7;
  color: #d97706;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
.priority-low {
  background-color: #d1fae5;
  color: #059669;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
.status-wait {
  background-color: #f3f4f6;
  color: #4b5563;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
.status-doing {
  background-color: #dbeafe;
  color: #2563eb;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
.status-finish {
  background-color: #d1fae5;
  color: #059669;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
.status-overdue {
  background-color: #fee2e2;
  color: #dc2626;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}
</style>