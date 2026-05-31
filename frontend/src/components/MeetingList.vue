<template>
  <div class="bg-white rounded-lg shadow-sm border overflow-hidden">
    <table class="w-full">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">组会标题</th>
          <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">类型</th>
          <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">时间</th>
          <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">地点</th>
          <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">汇报人</th>
          <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">状态</th>
          <th class="px-4 py-3 text-right text-sm font-medium text-gray-500">操作</th>
        </tr>
      </thead>
      <tbody class="divide-y">
        <tr v-for="m in meetings" :key="m.id" class="hover:bg-gray-50">
          <td class="px-4 py-3">
            <span class="font-medium">{{ m.title }}</span>
            <p v-if="m.description" class="text-sm text-gray-500 mt-1">{{ m.description }}</p>
          </td>
          <td class="px-4 py-3">
            <span :class="typeBadgeClass(m.meeting_type)">{{ typeText(m.meeting_type) }}</span>
          </td>
          <td class="px-4 py-3 text-sm">
            <div>{{ formatDate(m.scheduled_at) }}</div>
            <div class="text-gray-500">{{ formatTime(m.scheduled_at) }}</div>
          </td>
          <td class="px-4 py-3 text-sm">{{ m.location || '待定' }}</td>
          <td class="px-4 py-3">
            <div class="flex flex-wrap gap-1">
              <span v-for="p in (m.presenters || []).slice(0, 3)" :key="p.id" class="text-xs bg-gray-100 px-2 py-1 rounded">
                {{ p.username }}
              </span>
              <span v-if="(m.presenters || []).length > 3" class="text-xs text-gray-500">
                +{{ m.presenters.length - 3 }}
              </span>
            </div>
          </td>
          <td class="px-4 py-3">
            <span :class="statusBadgeClass(m.status)">{{ statusText(m.status) }}</span>
          </td>
          <td class="px-4 py-3 text-right">
            <div class="flex gap-2 justify-end">
              <button @click="$emit('view', m)" class="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 hover:bg-blue-200 flex items-center justify-center transition-colors" title="查看详情">
                <i class="fa fa-eye"></i>
              </button>
              <button v-if="canManage" @click="$emit('edit', m)" class="w-8 h-8 rounded-lg bg-orange-100 text-orange-600 hover:bg-orange-200 flex items-center justify-center transition-colors" title="编辑">
                <i class="fa fa-edit"></i>
              </button>
              <button v-if="canManage" @click="$emit('delete', m.id)" class="w-8 h-8 rounded-lg bg-red-100 text-red-600 hover:bg-red-200 flex items-center justify-center transition-colors" title="删除">
                <i class="fa fa-trash-o"></i>
              </button>
            </div>
          </td>
        </tr>
        <tr v-if="!meetings.length">
          <td colspan="7" class="px-4 py-8 text-center text-gray-500">暂无组会记录</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../stores/user'

defineProps({ meetings: Array })
defineEmits(['view', 'edit', 'delete'])

const userStore = useUserStore()

const canManage = computed(() => {
  return userStore.role === 'admin' || userStore.role === 'teacher'
})

function typeText(type) {
  const map = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }
  return map[type] || type
}

function typeBadgeClass(type) {
  const map = {
    regular: 'px-2 py-1 text-xs rounded bg-blue-100 text-blue-800',
    paper_reading: 'px-2 py-1 text-xs rounded bg-purple-100 text-purple-800',
    discussion: 'px-2 py-1 text-xs rounded bg-teal-100 text-teal-800'
  }
  return map[type] || 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-800'
}

function statusText(status) {
  const map = { scheduled: '待召开', ongoing: '进行中', completed: '已召开', cancelled: '已取消' }
  return map[status] || status
}

function statusBadgeClass(status) {
  const map = {
    scheduled: 'px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-800',
    ongoing: 'px-2 py-1 text-xs rounded bg-green-100 text-green-800',
    completed: 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-800',
    cancelled: 'px-2 py-1 text-xs rounded bg-red-100 text-red-800'
  }
  return map[status] || 'px-2 py-1 text-xs rounded bg-gray-100'
}

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
}

function formatTime(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}
</script>