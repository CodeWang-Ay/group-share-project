<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div v-for="m in meetings" :key="m.id" class="bg-white rounded-lg shadow-sm border overflow-hidden hover:shadow-md transition-shadow">
      <div :class="cardHeaderClass(m.meeting_type)" class="px-4 py-3">
        <div class="flex justify-between items-start">
          <span :class="typeBadgeClass(m.meeting_type)">{{ typeText(m.meeting_type) }}</span>
          <span :class="statusBadgeClass(m.status)">{{ statusText(m.status) }}</span>
        </div>
        <h3 class="font-bold mt-2">{{ m.title }}</h3>
      </div>
      <div class="p-4">
        <p v-if="m.description" class="text-sm text-gray-600 mb-3">{{ m.description }}</p>
        <div class="flex items-center gap-2 text-sm text-gray-500 mb-2">
          <i class="fa fa-calendar"></i>
          <span>{{ formatDate(m.scheduled_at) }} {{ formatTime(m.scheduled_at) }}</span>
        </div>
        <div class="flex items-center gap-2 text-sm text-gray-500 mb-3">
          <i class="fa fa-map-marker"></i>
          <span>{{ m.location || '地点待定' }}</span>
        </div>
        <div class="flex flex-wrap gap-2 mb-3">
          <div v-for="p in (m.presenters || []).slice(0, 3)" :key="p.id" class="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded text-sm">
            <div class="w-4 h-4 rounded-full bg-primary/20 flex items-center justify-center">
              <i class="fa fa-user text-xs text-primary"></i>
            </div>
            {{ p.username }}
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="$emit('edit', m)" class="px-3 py-1 text-sm border rounded hover:bg-gray-50">编辑</button>
          <button @click="$emit('delete', m.id)" class="px-3 py-1 text-sm text-red-500 border rounded hover:bg-red-50">删除</button>
        </div>
      </div>
    </div>
    <div v-if="!meetings.length" class="col-span-full text-center py-8 text-gray-500">
      暂无组会记录
    </div>
  </div>
</template>

<script setup>
defineProps({ meetings: Array })
defineEmits(['edit', 'delete'])

function typeText(type) {
  const map = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }
  return map[type] || type
}

function typeBadgeClass(type) {
  const map = {
    regular: 'px-2 py-0.5 text-xs rounded-full bg-blue-500 text-white',
    paper_reading: 'px-2 py-0.5 text-xs rounded-full bg-purple-500 text-white',
    discussion: 'px-2 py-0.5 text-xs rounded-full bg-teal-500 text-white'
  }
  return map[type] || 'px-2 py-0.5 text-xs rounded-full bg-gray-500 text-white'
}

function cardHeaderClass(type) {
  const map = {
    regular: 'bg-gradient-to-r from-blue-50 to-blue-100',
    paper_reading: 'bg-gradient-to-r from-purple-50 to-purple-100',
    discussion: 'bg-gradient-to-r from-teal-50 to-teal-100'
  }
  return map[type] || 'bg-gradient-to-r from-gray-50 to-gray-100'
}

function statusText(status) {
  const map = { scheduled: '待召开', ongoing: '进行中', completed: '已召开', cancelled: '已取消' }
  return map[status] || status
}

function statusBadgeClass(status) {
  const map = {
    scheduled: 'px-2 py-0.5 text-xs rounded bg-yellow-100 text-yellow-800',
    ongoing: 'px-2 py-0.5 text-xs rounded bg-green-100 text-green-800',
    completed: 'px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-800',
    cancelled: 'px-2 py-0.5 text-xs rounded bg-red-100 text-red-800'
  }
  return map[status] || 'px-2 py-0.5 text-xs rounded bg-gray-100'
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