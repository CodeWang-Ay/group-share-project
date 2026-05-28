<template>
  <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
    <table class="w-full">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">组会</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">汇报人</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">材料状态</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr v-if="meetings.length === 0">
          <td colspan="6" class="px-4 py-8 text-center text-gray-500">
            {{ searchKeyword ? `未找到包含 "${searchKeyword}" 的组会` : '暂无组会' }}
          </td>
        </tr>
        <tr v-for="m in meetings" :key="m.id" class="hover:bg-gray-50">
          <td class="px-4 py-3">
            <div class="font-medium text-gray-800">{{ m.title }}</div>
            <div v-if="m.description" class="text-xs text-gray-400 mt-1 truncate max-w-xs">{{ m.description }}</div>
          </td>
          <td class="px-4 py-3 text-sm text-gray-500">{{ formatDateTime(m.scheduled_at) }}</td>
          <td class="px-4 py-3 text-sm text-gray-500">{{ typeText(m.meeting_type) }}</td>
          <td class="px-4 py-3 text-sm text-gray-500">{{ presenterNames(m.presenters) }}</td>
          <td class="px-4 py-3">
            <span :class="materialStatusClass(m)" class="text-xs px-2 py-1 rounded-full">{{ materialStatusText(m) }}</span>
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <button @click="$emit('detail', m)" class="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 hover:bg-blue-200 flex items-center justify-center transition-colors" title="查看详情">
                <i class="fa fa-eye"></i>
              </button>
              <button @click="$emit('upload', m.id, m.title)" class="w-8 h-8 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 flex items-center justify-center transition-colors" title="上传材料">
                <i class="fa fa-upload"></i>
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  meetings: Array,
  searchKeyword: String
})

defineEmits(['detail', 'upload'])

function typeText(type) {
  const map = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }
  return map[type] || '未知'
}

function formatDateTime(dateStr) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function presenterNames(presenters) {
  if (!presenters || presenters.length === 0) return '暂无'
  const names = presenters.slice(0, 3).map(p => p.name || p.user?.username || '未知')
  return names.join(', ') + (presenters.length > 3 ? ` 等${presenters.length}人` : '')
}

function pendingCount(m) {
  const presenters = m.presenters || []
  return presenters.filter(p => !(p.files && p.files.length > 0)).length
}

function submittedCount(m) {
  const presenters = m.presenters || []
  return presenters.filter(p => p.files && p.files.length > 0 && p.material_status === 'pending').length
}

function materialStatusText(m) {
  const pending = pendingCount(m)
  const submitted = submittedCount(m)
  const presenters = m.presenters || []

  if (pending > 0) return `${pending}人待提交`
  if (submitted > 0) return `${submitted}人待审核`
  if (presenters.length > 0 && submitted === 0 && pending === 0) return '全部完成'
  return '暂无汇报人'
}

function materialStatusClass(m) {
  const pending = pendingCount(m)
  const submitted = submittedCount(m)
  const presenters = m.presenters || []

  if (pending > 0) return 'bg-orange-100 text-orange-600'
  if (submitted > 0) return 'bg-yellow-100 text-yellow-700'
  if (presenters.length > 0) return 'bg-green-100 text-green-600'
  return 'bg-gray-100 text-gray-500'
}
</script>