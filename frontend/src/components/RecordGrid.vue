<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
    <template v-if="records.length === 0">
      <div class="text-center py-12 text-gray-500 col-span-full">
        <p><i class="fa fa-folder-open-o text-4xl mb-4 block"></i>{{ emptyMessage() }}</p>
      </div>
    </template>
    <template v-else>
      <div v-for="m in records" :key="m.id" class="bg-white rounded-xl shadow-sm border p-5 flex flex-col min-h-[280px]">
        <!-- 头部标签 -->
        <div class="flex justify-between items-start mb-3">
          <span class="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded">第{{ weekNumber(m.scheduled_at) }}周组会 · {{ typeText(m.meeting_type) }}</span>
          <span class="text-gray-400 text-sm">{{ formatDate(m.scheduled_at) }}</span>
        </div>
        <!-- 标题 -->
        <h3 class="font-semibold text-gray-800 mb-2">{{ m.title }}</h3>
        <!-- 纪要摘要 -->
        <p class="text-sm text-gray-500 overflow-hidden h-10 mb-4">{{ summaryText(m) }}</p>
        <!-- 汇报人和纪要状态 -->
        <div class="flex items-center justify-between text-sm text-gray-500 mb-3">
          <div class="flex items-center gap-2">
            <i class="fa fa-users"></i>
            <span>汇报人：{{ presenterNames(m.presenters) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="m.minutes" class="text-green-600"><i class="fa fa-check-circle"></i> 已填写纪要</span>
            <span v-else class="text-orange-500"><i class="fa fa-exclamation-circle"></i> 待填写纪要</span>
          </div>
        </div>
        <!-- 汇报材料区域 -->
        <div class="flex-1 min-h-[40px]">
          <div class="flex justify-between items-center mb-1">
            <p class="text-xs text-gray-400"><i class="fa fa-file-text-o mr-1"></i>汇报材料</p>
            <button @click="loadMaterials(m.id)" class="text-xs text-primary hover:underline">加载材料</button>
          </div>
          <div :id="'materials-' + m.id" class="text-xs text-gray-400">
            {{ materialsText(m.id) }}
          </div>
        </div>
        <!-- 底部操作区域 -->
        <div class="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <i class="fa fa-clock-o"></i>
            <span>{{ m.duration_total }}分钟</span>
          </div>
          <div class="flex gap-2">
            <button @click="$emit('view', m)" class="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 hover:bg-blue-200 flex items-center justify-center transition-colors" title="查看详情">
              <i class="fa fa-eye"></i>
            </button>
            <button v-if="canEdit" @click="$emit('edit', m.id, m.title, m.minutes)" class="w-8 h-8 rounded-lg bg-green-100 text-green-600 hover:bg-green-200 flex items-center justify-center transition-colors" title="编辑纪要">
              <i class="fa fa-edit"></i>
            </button>
            <button @click="$emit('loadMaterials', m.id)" class="w-8 h-8 rounded-lg bg-purple-100 text-purple-600 hover:bg-purple-200 flex items-center justify-center transition-colors" title="查看材料">
              <i class="fa fa-file-text-o"></i>
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { recordApi } from '../api/record'

const props = defineProps({
  records: Array,
  searchKeyword: String,
  minutesFilter: String
})

defineEmits(['view', 'edit', 'loadMaterials'])

const userStore = useUserStore()

const canEdit = computed(() => {
  return userStore.role === 'admin' || userStore.role === 'teacher'
})

const typeMap = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }
const loadedMaterials = ref({})

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

function summaryText(m) {
  if (m.minutes) {
    let text = m.minutes
      .replace(/```[\s\S]*?```/g, '')
      .replace(/---+/g, '')
      .replace(/\|[^|]+\|/g, '')
      .replace(/^#+ .*/gm, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/[*_`~>#-]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
    if (text.length > 60) text = text.substring(0, 60) + '...'
    return text || '已填写纪要'
  }
  if (m.description) {
    const text = m.description
    return text.length > 60 ? text.substring(0, 60) + '...' : text
  }
  return '暂无会议纪要'
}

function materialsText(meetingId) {
  const materials = loadedMaterials.value[meetingId]
  if (!materials) return '点击加载查看'
  if (materials.length === 0) return '暂无材料'
  return materials.map(f => f.filename).join(', ')
}

async function loadMaterials(meetingId) {
  const m = props.records.find(r => r.id === meetingId)
  if (!m || !m.presenters) return

  const files = []
  for (const p of m.presenters) {
    try {
      const res = await recordApi.getPresenterFiles(p.id)
      if (res.data.files) {
        files.push(...res.data.files)
      }
    } catch (e) {
      console.error('加载材料失败:', e)
    }
  }
  loadedMaterials.value[meetingId] = files
}
</script>