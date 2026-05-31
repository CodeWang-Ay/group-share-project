<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col overflow-hidden">
      <!-- 标题栏（固定） -->
      <div class="p-4 border-b flex justify-between items-center shrink-0">
        <h3 class="font-semibold text-lg">进展详情</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <!-- 内容区域（可滚动） -->
      <div class="p-4 space-y-4 overflow-y-auto flex-1">
        <!-- 研究方向和状态 -->
        <div class="flex justify-between items-start pb-3 border-b border-gray-100">
          <div>
            <p class="font-semibold text-gray-800">{{ progressData?.research_direction }}</p>
            <p class="text-sm text-gray-500">提交时间：{{ formatDate(progressData?.created_at) }}</p>
            <p class="text-sm text-gray-500">更新时间：{{ formatDate(progressData?.updated_at) }}</p>
          </div>
          <span :class="statusClass">{{ statusText }}</span>
        </div>

        <!-- 本周进展（蓝色） -->
        <div class="bg-blue-50 rounded-lg p-4 border border-blue-100">
          <div class="flex items-center gap-2 mb-2">
            <i class="fa fa-file-text-o text-blue-500"></i>
            <span class="font-medium text-blue-700">本周进展</span>
          </div>
          <p class="text-gray-600">{{ progressData?.weekly_progress || '-' }}</p>
        </div>

        <!-- 下周计划（绿色） -->
        <div class="bg-green-50 rounded-lg p-4 border border-green-100">
          <div class="flex items-center gap-2 mb-2">
            <i class="fa fa-flag text-green-500"></i>
            <span class="font-medium text-green-700">下周计划</span>
          </div>
          <p class="text-gray-600">{{ progressData?.next_goal || '-' }}</p>
        </div>

        <!-- 遇到的困难（橙色） -->
        <div class="bg-orange-50 rounded-lg p-4 border border-orange-100">
          <div class="flex items-center gap-2 mb-2">
            <i class="fa fa-exclamation-circle text-orange-500"></i>
            <span class="font-medium text-orange-700">遇到的困难</span>
          </div>
          <p class="text-gray-600">{{ progressData?.difficulties || '-' }}</p>
        </div>

        <!-- 完成度 -->
        <div class="bg-gray-50 rounded-lg p-4 border border-gray-100">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <i class="fa fa-tasks text-gray-500"></i>
              <span class="font-medium text-gray-700">完成度</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-20 bg-gray-200 rounded-full h-2">
                <div class="bg-primary h-2 rounded-full" :style="{ width: (progressData?.completion_rate || 0) + '%' }"></div>
              </div>
              <span class="text-gray-700 font-medium">{{ progressData?.completion_rate }}%</span>
            </div>
          </div>
        </div>

        <!-- 附件 -->
        <div v-if="progressData?.attachments && progressData?.attachments.length > 0" class="bg-gray-50 rounded-lg p-4 border border-gray-100">
          <div class="flex items-center gap-2 mb-3">
            <i class="fa fa-paperclip text-gray-500"></i>
            <span class="font-medium text-gray-700">附件（{{ progressData.attachments.length }} 个）</span>
          </div>
          <div class="space-y-2">
            <div v-for="filename in progressData.attachments" :key="filename"
                 class="flex items-center justify-between p-2 bg-white rounded">
              <div class="flex items-center gap-2">
                <div :class="getFileIconClass(filename)" class="w-8 h-8 rounded flex items-center justify-center">
                  <i class="fa fa-file-o"></i>
                </div>
                <span class="text-sm text-gray-700 truncate max-w-[200px]">{{ filename }}</span>
              </div>
              <a :href="getFileUrl(filename)" target="_blank"
                 class="px-3 py-1 bg-primary text-white text-xs rounded hover:bg-primary/90">
                <i class="fa fa-download mr-1"></i>下载
              </a>
            </div>
          </div>
        </div>
        <div v-else class="bg-gray-50 rounded-lg p-4 border border-gray-100">
          <div class="flex items-center gap-2">
            <i class="fa fa-paperclip text-gray-400"></i>
            <span class="text-sm text-gray-500">暂无附件</span>
          </div>
        </div>

        <!-- 导师反馈 -->
        <div v-if="progressData?.supervisor_feedback" class="bg-purple-50 rounded-lg p-4 border border-purple-100">
          <div class="flex items-center gap-2 mb-2">
            <i class="fa fa-comment text-purple-500"></i>
            <span class="font-medium text-purple-700">导师反馈{{ progressData?.feedback_by_name ? `（${progressData.feedback_by_name}）` : '' }}</span>
          </div>
          <p class="text-gray-600">{{ progressData.supervisor_feedback }}</p>
        </div>
      </div>

      <!-- 底部反馈区域（固定） -->
      <div v-if="isTeacher" class="p-4 border-t shrink-0 bg-gray-50">
        <label class="block text-sm font-medium text-gray-700 mb-1">发送反馈</label>
        <textarea v-model="feedbackInput" rows="2" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50" placeholder="输入反馈内容..."></textarea>
        <button @click="sendFeedback" class="mt-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
          发送反馈
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { getFileDownloadUrl } from '../api/research_progress'

const props = defineProps({
  visible: Boolean,
  progressData: Object,
  isTeacher: Boolean
})

const emit = defineEmits(['update:modelValue', 'send-feedback'])

const userStore = useUserStore()
const visible = defineModel()
const feedbackInput = ref('')

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  // 处理时间字符串，确保显示北京时间
  const date = new Date(dateStr)
  // 如果时间字符串没有时区信息，假设是北京时间（UTC+8）
  if (!dateStr.includes('Z') && !dateStr.includes('+') && !dateStr.includes('T')) {
    // 简单的日期格式，直接显示
    return dateStr
  }
  // 使用北京时间格式化
  const options = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Shanghai'
  }
  return new Intl.DateTimeFormat('zh-CN', options).format(date)
}

const statusClass = computed(() => {
  const status = props.progressData?.status
  const map = {
    normal: 'px-2 py-0.5 bg-green-100 text-green-600 rounded-full text-xs',
    delayed: 'px-2 py-0.5 bg-orange-100 text-orange-500 rounded-full text-xs',
    not_updated: 'px-2 py-0.5 bg-red-100 text-red-500 rounded-full text-xs'
  }
  return map[status] || map.normal
})

const statusText = computed(() => {
  const status = props.progressData?.status
  const map = { normal: '正常', delayed: '延迟', not_updated: '未更新' }
  return map[status] || '正常'
})

// 获取带 token 的下载 URL
const getFileUrl = (filename) => {
  const baseUrl = getFileDownloadUrl(filename)
  const token = userStore.token
  if (token) {
    return `${baseUrl}?session_token=${encodeURIComponent(token)}`
  }
  return baseUrl
}

// 根据文件类型返回图标样式
const getFileIconClass = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  const typeMap = {
    pdf: 'text-red-500 bg-red-50',
    doc: 'text-blue-500 bg-blue-50',
    docx: 'text-blue-500 bg-blue-50',
    ppt: 'text-orange-500 bg-orange-50',
    pptx: 'text-orange-500 bg-orange-50',
    xls: 'text-green-500 bg-green-50',
    xlsx: 'text-green-500 bg-green-50',
    zip: 'text-purple-500 bg-purple-50',
    rar: 'text-purple-500 bg-purple-50',
    jpg: 'text-yellow-500 bg-yellow-50',
    png: 'text-yellow-500 bg-yellow-50',
    mp4: 'text-pink-500 bg-pink-50'
  }
  return typeMap[ext] || 'text-gray-500 bg-gray-50'
}

const sendFeedback = () => {
  if (!feedbackInput.value) return
  emit('send-feedback', feedbackInput.value)
  feedbackInput.value = ''
}

const close = () => {
  visible.value = false
}
</script>