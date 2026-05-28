<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
    <template v-if="meetings.length === 0">
      <div class="text-center py-12 text-gray-500 col-span-full">
        <p>{{ searchKeyword ? `未找到包含 "${searchKeyword}" 的组会` : '暂无组会' }}</p>
      </div>
    </template>
    <template v-else>
      <div v-for="m in meetings" :key="m.id" class="bg-white rounded-2xl shadow-md border overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group h-full flex flex-col">
        <!-- 卡片顶部渐变条 -->
        <div :class="typeColorClass(m.meeting_type)" class="h-2"></div>

        <!-- 卡片主体 -->
        <div class="p-5 flex-1 flex flex-col">
          <!-- 状态和类型标签 -->
          <div class="flex items-center gap-2 mb-3">
            <span :class="statusClass(m.status)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ statusText(m.status) }}</span>
            <span class="bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full">{{ typeText(m.meeting_type) }}</span>
            <span v-if="materialBadge(m)" :class="materialBadgeClass(m)" class="text-xs px-2 py-0.5 rounded-full">{{ materialBadge(m) }}</span>
          </div>

          <!-- 标题 -->
          <h3 class="text-base font-semibold text-gray-800 mb-2 line-clamp-2 group-hover:text-primary transition-colors">{{ m.title }}</h3>

          <!-- 时间地点 -->
          <div class="flex items-center gap-4 text-sm text-gray-500 mb-3">
            <span class="flex items-center gap-1"><i class="fa fa-calendar text-gray-400"></i>{{ formatDate(m.scheduled_at) }}</span>
            <span class="flex items-center gap-1"><i class="fa fa-clock-o text-gray-400"></i>{{ formatTime(m.scheduled_at) }}</span>
          </div>

          <div v-if="m.location" class="flex items-center gap-1 text-sm text-gray-500 mb-3">
            <i class="fa fa-map-marker text-gray-400"></i>
            <span class="truncate">{{ m.location }}</span>
          </div>
          <div v-else class="flex items-center gap-1 text-sm text-gray-400 mb-3 h-5">
            <span>地点待定</span>
          </div>

          <!-- 汇报人数量 -->
          <div class="flex items-center gap-2 text-sm text-gray-500 mb-3">
            <i class="fa fa-users text-gray-400"></i>
            <span>{{ (m.presenters || []).length }} 位汇报人</span>
          </div>

          <!-- 材料提交进度 -->
          <div v-if="(m.presenters || []).length > 0" class="mt-auto">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>材料提交进度</span>
              <span>{{ approvedCount(m) }}/{{ (m.presenters || []).length }}</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-2">
              <div class="bg-green-500 h-2 rounded-full transition-all" :style="{ width: approvedPercent(m) + '%' }"></div>
            </div>
          </div>
          <p v-else class="text-xs text-gray-400 mt-auto"><i class="fa fa-user-o mr-1"></i>暂无汇报人</p>

          <!-- 底部操作按钮 -->
          <div class="mt-3 pt-3 border-t border-gray-100 flex justify-center gap-3">
            <button @click="$emit('detail', m)" class="flex items-center gap-1 px-3 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors text-sm">
              <i class="fa fa-eye"></i> 详情
            </button>
            <button @click="$emit('upload', m.id, m.title)" class="flex items-center gap-1 px-3 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors text-sm">
              <i class="fa fa-upload"></i> 上传
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  meetings: Array,
  searchKeyword: String
})

defineEmits(['detail', 'upload'])

function statusText(status) {
  const map = { scheduled: '待召开', ongoing: '进行中', completed: '已召开', cancelled: '已废弃' }
  return map[status] || '未知'
}

function statusClass(status) {
  const map = {
    scheduled: 'bg-blue-100 text-blue-700',
    ongoing: 'bg-green-100 text-green-700',
    completed: 'bg-gray-100 text-gray-700',
    cancelled: 'bg-red-100 text-red-700'
  }
  return map[status] || 'bg-gray-100 text-gray-600'
}

function typeText(type) {
  const map = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }
  return map[type] || '未知'
}

function typeColorClass(type) {
  const map = {
    regular: 'bg-gradient-to-r from-blue-500 to-blue-600',
    paper_reading: 'bg-gradient-to-r from-purple-500 to-purple-600',
    discussion: 'bg-gradient-to-r from-teal-500 to-teal-600'
  }
  return map[type] || 'bg-gradient-to-r from-gray-500 to-gray-600'
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function formatTime(dateStr) {
  const d = new Date(dateStr)
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function pendingCount(m) {
  const presenters = m.presenters || []
  return presenters.filter(p => !(p.files && p.files.length > 0)).length
}

function submittedCount(m) {
  const presenters = m.presenters || []
  return presenters.filter(p => p.files && p.files.length > 0 && p.material_status === 'pending').length
}

function approvedCount(m) {
  const presenters = m.presenters || []
  return presenters.filter(p => p.files && p.files.length > 0 && p.material_status === 'approved').length
}

function approvedPercent(m) {
  const total = (m.presenters || []).length
  return total > 0 ? (approvedCount(m) / total * 100) : 0
}

function materialBadge(m) {
  const pending = pendingCount(m)
  const submitted = submittedCount(m)
  const approved = approvedCount(m)
  const total = (m.presenters || []).length

  if (pending > 0) return `${pending}人待提交`
  if (submitted > 0) return `${submitted}人待审核`
  if (approved === total && total > 0) return '全部完成'
  return ''
}

function materialBadgeClass(m) {
  const pending = pendingCount(m)
  const submitted = submittedCount(m)

  if (pending > 0) return 'bg-orange-100 text-orange-600'
  if (submitted > 0) return 'bg-yellow-100 text-yellow-700'
  return 'bg-green-100 text-green-600'
}
</script>