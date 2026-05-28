<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
      <div class="p-4 border-b flex justify-between items-center">
        <h3 class="font-semibold text-lg">进展详情</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <div class="p-4 space-y-3">
        <div class="flex justify-between items-start">
          <div>
            <p class="font-semibold text-gray-800">{{ progressData?.research_direction }}</p>
            <p class="text-sm text-gray-500">提交时间：{{ formatDate(progressData?.created_at) }}</p>
          </div>
          <span :class="statusClass">{{ statusText }}</span>
        </div>

        <div class="bg-gray-50 rounded-lg p-3 space-y-2">
          <p class="text-sm text-gray-600"><strong>本周进展：</strong>{{ progressData?.weekly_progress }}</p>
          <p class="text-sm text-gray-600"><strong>下周计划：</strong>{{ progressData?.next_goal || '-' }}</p>
          <p class="text-sm text-gray-600"><strong>遇到的困难：</strong>{{ progressData?.difficulties || '-' }}</p>
          <p class="text-sm text-gray-600"><strong>完成度：</strong>{{ progressData?.completion_rate }}%</p>
        </div>

        <!-- 附件 -->
        <div v-if="progressData?.attachments && progressData?.attachments.length > 0">
          <p class="text-sm text-gray-700"><strong>附件：</strong></p>
          <div class="mt-1 flex flex-wrap gap-2">
            <a v-for="filename in progressData.attachments" :key="filename"
               :href="getFileUrl(filename)" target="_blank"
               class="inline-flex items-center px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm text-primary">
              <i class="fa fa-file-o mr-2"></i>{{ filename }}
            </a>
          </div>
        </div>

        <!-- 导师反馈 -->
        <div v-if="progressData?.supervisor_feedback" class="p-3 bg-blue-50 rounded-lg">
          <p class="text-sm text-gray-500 mb-1">导师反馈{{ progressData?.feedback_by_name ? `（${progressData.feedback_by_name}）` : '' }}：</p>
          <p class="text-gray-700">{{ progressData.supervisor_feedback }}</p>
        </div>

        <!-- 导师发送反馈 -->
        <div v-if="isTeacher" class="border-t pt-3">
          <label class="block text-sm font-medium text-gray-700 mb-1">发送反馈</label>
          <textarea v-model="feedbackInput" rows="2" class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50" placeholder="输入反馈内容..."></textarea>
          <button @click="sendFeedback" class="mt-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
            发送反馈
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { getFileDownloadUrl } from '../api/research_progress'

const props = defineProps({
  visible: Boolean,
  progressData: Object,
  isTeacher: Boolean
})

const emit = defineEmits(['update:modelValue', 'send-feedback'])

const visible = defineModel()
const feedbackInput = ref('')

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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

const getFileUrl = (filename) => getFileDownloadUrl(filename)

const sendFeedback = () => {
  if (!feedbackInput.value) return
  emit('send-feedback', feedbackInput.value)
  feedbackInput.value = ''
}

const close = () => {
  visible.value = false
}
</script>