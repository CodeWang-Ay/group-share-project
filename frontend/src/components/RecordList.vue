<template>
  <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
    <table class="w-full">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">组会标题</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">纪要状态</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">汇报人</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr v-if="records.length === 0">
          <td colspan="5" class="px-4 py-8 text-center text-gray-500">
            {{ emptyMessage() }}
          </td>
        </tr>
        <tr v-for="m in records" :key="m.id" class="hover:bg-gray-50">
          <td class="px-4 py-3">
            <div class="font-medium text-gray-800">{{ m.title }}</div>
            <div class="text-xs text-gray-400 mt-1">第{{ weekNumber(m.scheduled_at) }}周 · {{ typeText(m.meeting_type) }}</div>
          </td>
          <td class="px-4 py-3 text-sm text-gray-500">{{ formatDate(m.scheduled_at) }}</td>
          <td class="px-4 py-3">
            <span v-if="m.minutes" class="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">已填写</span>
            <span v-else class="bg-orange-100 text-orange-600 text-xs px-2 py-1 rounded-full">待填写</span>
          </td>
          <td class="px-4 py-3 text-sm text-gray-500">{{ presenterNames(m.presenters) }}</td>
          <td class="px-4 py-3">
            <div class="flex gap-2">
              <button @click="$emit('view', m)" class="text-primary hover:underline text-sm">查看</button>
              <button @click="$emit('edit', m.id, m.title, m.minutes)" class="text-green-600 hover:underline text-sm">编辑纪要</button>
              <button @click="$emit('materials', m.id, m.title)" class="text-purple-600 hover:underline text-sm">材料</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  records: Array,
  searchKeyword: String,
  minutesFilter: String
})

defineEmits(['view', 'edit', 'materials'])

const typeMap = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }

function emptyMessage() {
  if (props.searchKeyword) return `未找到包含 "${props.searchKeyword}" 的记录`
  if (props.minutesFilter === 'filled') return '暂无已填写纪要的记录'
  if (props.minutesFilter === 'empty') return '暂无待填写纪要的记录'
  return '暂无组会记录'
}

function typeText(type) {
  return typeMap[type] || '常规组会'
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function weekNumber(dateStr) {
  const d = new Date(dateStr)
  return Math.ceil(d.getDate() / 7)
}

function presenterNames(presenters) {
  if (!presenters || presenters.length === 0) return '暂无'
  return presenters.map(p => p.real_name || p.username || '未知').join('、')
}
</script>