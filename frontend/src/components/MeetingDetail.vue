<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 overflow-hidden max-h-[90vh] flex flex-col">
      <!-- 头部 -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
        <h2 class="text-lg font-semibold text-gray-800">组会详情</h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="p-6 overflow-y-auto flex-1">
        <!-- 基本信息 -->
        <div class="flex items-center gap-3 mb-4">
          <span :class="statusBadgeClass">{{ statusText }}</span>
          <span :class="typeBadgeClass">{{ typeText }}</span>
        </div>
        <h3 class="text-xl font-bold text-gray-800 mb-4">{{ meeting?.title }}</h3>

        <!-- 详细信息 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <i class="fa fa-calendar text-primary"></i>
              </div>
              <div>
                <p class="text-sm text-gray-500">会议时间</p>
                <p class="font-medium text-gray-800">{{ formatDate(meeting?.scheduled_at) }} {{ formatTime(meeting?.scheduled_at) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                <i class="fa fa-clock-o text-green-600"></i>
              </div>
              <div>
                <p class="text-sm text-gray-500">会议时长</p>
                <p class="font-medium text-gray-800">{{ meeting?.duration || '--' }}分钟</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <i class="fa fa-map-marker text-purple-600"></i>
              </div>
              <div>
                <p class="text-sm text-gray-500">会议地点</p>
                <p class="font-medium text-gray-800">{{ meeting?.location || '待定' }}</p>
              </div>
            </div>
          </div>
          <div class="space-y-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                <i class="fa fa-user text-indigo-600"></i>
              </div>
              <div>
                <p class="text-sm text-gray-500">创建者</p>
                <p class="font-medium text-gray-800">{{ meeting?.creator_name || '系统' }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                <i class="fa fa-file-text-o text-orange-600"></i>
              </div>
              <div>
                <p class="text-sm text-gray-500">组会类型</p>
                <p class="font-medium text-gray-800">{{ typeText }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                <i class="fa fa-calendar-plus-o text-gray-600"></i>
              </div>
              <div>
                <p class="text-sm text-gray-500">创建时间</p>
                <p class="font-medium text-gray-800">{{ formatDate(meeting?.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 描述 -->
        <div class="mt-6 p-4 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-500 mb-2">组会描述</p>
          <p class="text-gray-800 max-h-32 overflow-y-auto whitespace-pre-wrap break-words">{{ meeting?.description || '暂无描述' }}</p>
        </div>

        <!-- 汇报人列表 -->
        <div class="mt-6 p-4 bg-green-50 rounded-lg">
          <p class="text-sm text-gray-500 mb-3">汇报人</p>
          <div class="space-y-2">
            <div v-if="presenters.length === 0" class="text-sm text-gray-400">
              暂无汇报人
            </div>
            <div v-for="p in presenters" :key="p.id" class="flex items-center gap-3 p-2 bg-white rounded-lg">
              <img :src="getAvatarUrl(p.avatar, p.username)" class="w-8 h-8 rounded-full object-cover">
              <div class="flex-1">
                <p class="font-medium text-gray-800">{{ p.real_name || p.username }}</p>
                <p class="text-xs text-gray-500">{{ p.degree_type || '' }}</p>
              </div>
              <span class="text-xs text-gray-500">{{ p.duration || '--' }}分钟</span>
            </div>
          </div>
        </div>

        <!-- 当前状态 -->
        <div class="mt-6 p-4 bg-blue-50 rounded-lg">
          <p class="text-sm text-gray-500 mb-2">当前状态</p>
          <div class="flex items-center gap-2">
            <i :class="statusIconClass"></i>
            <span class="font-medium">{{ statusText }}</span>
            <span v-if="meeting?.status === 'scheduled'" class="text-sm text-gray-500 ml-2">
              （{{ daysUntilMeeting }}天后召开）
            </span>
          </div>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 flex-shrink-0">
        <button @click="close" class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors">
          关闭
        </button>
        <button v-if="canEdit" @click="$emit('edit', meeting)" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
          <i class="fa fa-edit mr-1"></i>编辑
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../stores/user'
import { getAvatarUrl } from '../config'

const props = defineProps({
  visible: Boolean,
  meeting: Object
})
const emit = defineEmits(['close', 'edit'])

const userStore = useUserStore()

const visible = defineModel()

const presenters = computed(() => props.meeting?.presenters || [])

const canEdit = computed(() => {
  // 只有导师和管理员可以编辑
  return userStore.role === 'admin' || userStore.role === 'teacher'
})

const statusText = computed(() => {
  const map = {
    scheduled: '待召开',
    ongoing: '进行中',
    completed: '已召开',
    cancelled: '已废弃'
  }
  return map[props.meeting?.status] || '未知'
})

const typeText = computed(() => {
  const map = {
    regular: '常规组会',
    paper_reading: '论文研读',
    discussion: '专题讨论'
  }
  return map[props.meeting?.meeting_type] || '未知类型'
})

const statusBadgeClass = computed(() => {
  const map = {
    scheduled: 'px-3 py-1 text-sm rounded-full bg-orange-100 text-orange-700',
    ongoing: 'px-3 py-1 text-sm rounded-full bg-green-100 text-green-700',
    completed: 'px-3 py-1 text-sm rounded-full bg-gray-100 text-gray-700',
    cancelled: 'px-3 py-1 text-sm rounded-full bg-red-100 text-red-700'
  }
  return map[props.meeting?.status] || 'px-3 py-1 text-sm rounded-full bg-gray-100'
})

const typeBadgeClass = computed(() => {
  const map = {
    regular: 'px-3 py-1 text-sm rounded-full bg-blue-100 text-blue-700',
    paper_reading: 'px-3 py-1 text-sm rounded-full bg-purple-100 text-purple-700',
    discussion: 'px-3 py-1 text-sm rounded-full bg-teal-100 text-teal-700'
  }
  return map[props.meeting?.meeting_type] || 'px-3 py-1 text-sm rounded-full bg-gray-100'
})

const statusIconClass = computed(() => {
  const map = {
    scheduled: 'fa fa-clock-o text-orange-500',
    ongoing: 'fa fa-play-circle text-green-500',
    completed: 'fa fa-check-circle text-gray-500',
    cancelled: 'fa fa-times-circle text-red-500'
  }
  return map[props.meeting?.status] || 'fa fa-question-circle text-gray-500'
})

const daysUntilMeeting = computed(() => {
  if (!props.meeting?.scheduled_at) return 0
  const meetingDate = new Date(props.meeting.scheduled_at)
  const today = new Date()
  const diff = meetingDate.getTime() - today.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
})

function formatDate(d) {
  if (!d) return '--'
  const date = new Date(d)
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
}

function formatTime(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}

function close() {
  visible.value = false
}
</script>