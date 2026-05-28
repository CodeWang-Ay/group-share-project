<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-2xl w-full mx-4 overflow-hidden">
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <h2 class="text-lg font-bold text-gray-800">组会材料详情</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>
      <div class="p-6">
        <div class="space-y-4">
          <!-- 组会基本信息 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-3">
              <span :class="statusClass(meeting.status)" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ statusText(meeting.status) }}</span>
              <span class="bg-gray-200 text-gray-500 text-xs px-2 py-0.5 rounded-full">{{ typeText(meeting.meeting_type) }}</span>
            </div>
            <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ meeting.title }}</h3>
            <div class="flex items-center gap-4 text-sm text-gray-500 mb-2">
              <span class="flex items-center gap-1"><i class="fa fa-calendar text-gray-400"></i>{{ formatDateTime(meeting.scheduled_at) }}</span>
              <span v-if="meeting.location" class="flex items-center gap-1"><i class="fa fa-map-marker text-gray-400"></i>{{ meeting.location }}</span>
            </div>
            <p v-if="meeting.description" class="text-sm text-gray-600">{{ meeting.description }}</p>
          </div>

          <!-- 汇报人材料状态 -->
          <div>
            <h4 class="text-sm font-medium text-gray-700 mb-3">汇报人材料状态 ({{ presenters.length }}人)</h4>
            <div v-if="presenters.length === 0" class="text-sm text-gray-400 text-center py-4">暂无汇报人</div>
            <div v-else class="space-y-2">
              <div v-for="p in presenters" :key="p.id" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-sm">
                    <i class="fa fa-user"></i>
                  </div>
                  <div>
                    <p class="font-medium text-gray-800">{{ p.name || p.user?.username || '未知' }}</p>
                    <p class="text-xs text-gray-500">{{ p.duration_minutes }}分钟 · {{ p.presenter_type === 'assigned' ? '导师指定' : '主动报名' }}</p>
                    <div class="mt-1">
                      <template v-if="p.files && p.files.length > 0">
                        <span v-for="f in p.files" :key="f.id" class="text-xs text-gray-500 mr-2"><i class="fa fa-file-o"></i>{{ f.filename }}</span>
                      </template>
                      <span v-else class="text-xs text-gray-400">未上传</span>
                    </div>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <span :class="confirmStatusClass(p.status)" class="text-xs px-2 py-1 rounded-full">{{ confirmStatusText(p.status) }}</span>
                  <span :class="materialStatusClass(p)" class="text-xs px-2 py-1 rounded-full">{{ materialStatusText(p) }}</span>
                  <button v-if="canConfirm(p)" @click="$emit('confirm', p.id)" class="px-2 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700">
                    <i class="fa fa-check"></i> 确认
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="px-6 py-4 border-t flex justify-end">
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  meeting: Object,
  userId: Number
})

defineEmits(['close', 'confirm'])

const presenters = computed(() => props.meeting?.presenters || [])

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

function formatDateTime(dateStr) {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}

function confirmStatusClass(status) {
  return status === 'confirmed' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-600'
}

function confirmStatusText(status) {
  return status === 'confirmed' ? '已确认' : '待确认'
}

function materialStatusClass(p) {
  const hasFiles = p.files && p.files.length > 0
  if (!hasFiles) return 'bg-orange-100 text-orange-600'
  if (p.material_status === 'pending') return 'bg-yellow-100 text-yellow-700'
  if (p.material_status === 'approved') return 'bg-green-100 text-green-600'
  return 'bg-red-100 text-red-600'
}

function materialStatusText(p) {
  const hasFiles = p.files && p.files.length > 0
  if (!hasFiles) return '待提交'
  if (p.material_status === 'pending') return '待审核'
  if (p.material_status === 'approved') return '已通过'
  return '已驳回'
}

function canConfirm(p) {
  const presenterUserId = p.user_id || p.user?.id
  return props.userId && presenterUserId === props.userId && p.status === 'pending'
}
</script>