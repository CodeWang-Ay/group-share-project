<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-4xl w-full mx-4 max-h-[85vh] flex flex-col overflow-hidden">
      <!-- 头部 -->
      <div class="px-6 py-4 border-b flex-shrink-0">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-bold text-gray-800">汇报材料</h2>
            <p class="text-sm text-gray-500">{{ meetingTitle }}</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-500">{{ submittedCount }}/{{ presenterMaterials.length }} 人已提交</span>
            <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
              <i class="fa fa-times text-xl"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- 内容 -->
      <div class="flex-1 overflow-y-auto p-6">
        <div v-if="loading" class="text-center py-8 text-gray-500"><i class="fa fa-spinner fa-spin"></i> 加载中...</div>
        <div v-else-if="presenterMaterials.length === 0" class="text-center py-8 text-gray-500">暂无汇报人</div>
        <div v-else class="space-y-4">
          <!-- 按汇报人分组显示 -->
          <div v-for="pm in presenterMaterials" :key="pm.presenterId" class="bg-gray-50 rounded-lg p-4">
            <div class="flex justify-between items-center mb-3">
              <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <i class="fa fa-user"></i>
                </div>
                <span class="font-medium text-gray-800">{{ pm.presenterName }}</span>
                <span class="text-xs text-gray-500">{{ pm.durationMinutes }}分钟</span>
              </div>
              <span v-if="pm.files.length > 0" class="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                <i class="fa fa-check-circle mr-1"></i>{{ pm.files.length }} 个文件
              </span>
              <span v-else class="bg-orange-100 text-orange-600 text-xs px-2 py-1 rounded-full">
                <i class="fa fa-exclamation-circle mr-1"></i>未提交
              </span>
            </div>

            <!-- 文件列表 -->
            <div v-if="pm.files.length > 0" class="space-y-2 pl-10">
              <div v-for="f in pm.files" :key="f.id" class="flex items-center justify-between p-2 bg-white rounded">
                <div class="flex items-center gap-3">
                  <div :class="fileIconClass(f.file_type)" class="w-8 h-8 rounded flex items-center justify-center">
                    <i class="fa fa-file-o"></i>
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-800">{{ f.filename }}</p>
                    <p class="text-xs text-gray-500">{{ formatSize(f.file_size) }}</p>
                  </div>
                </div>
                <button @click="downloadFile(f.id, f.filename)" class="text-sm text-primary hover:underline">
                  <i class="fa fa-download"></i> 下载
                </button>
              </div>
            </div>
            <div v-else class="pl-10 text-sm text-gray-400 italic">暂无提交材料</div>
          </div>
        </div>
      </div>

      <!-- 底部 -->
      <div class="px-6 py-4 border-t flex justify-between items-center flex-shrink-0 bg-white">
        <div class="text-sm text-gray-500">
          <span class="text-green-600">{{ submittedCount }} 人已提交</span>
          <span class="mx-2">·</span>
          <span class="text-orange-500">{{ presenterMaterials.length - submittedCount }} 人未提交</span>
        </div>
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { recordApi } from '../api/record'

const props = defineProps({
  meetingId: Number,
  meetingTitle: String
})

defineEmits(['close'])

const loading = ref(true)
const presenterMaterials = ref([]) // 按汇报人分组的材料数据

const fileTypeMap = {
  pdf: 'text-red-500 bg-red-50',
  doc: 'text-blue-500 bg-blue-50',
  docx: 'text-blue-500 bg-blue-50',
  ppt: 'text-orange-500 bg-orange-50',
  pptx: 'text-orange-500 bg-orange-50',
  xls: 'text-green-500 bg-green-50',
  xlsx: 'text-green-500 bg-green-50'
}

function fileIconClass(type) {
  return fileTypeMap[type] || 'text-gray-500 bg-gray-50'
}

function formatSize(size) {
  if (!size) return '未知'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

// 已提交人数统计
const submittedCount = computed(() => {
  return presenterMaterials.value.filter(pm => pm.files.length > 0).length
})

async function loadMaterials() {
  loading.value = true
  presenterMaterials.value = []
  try {
    const res = await recordApi.getMeetingDetail(props.meetingId)
    if (res.data.success) {
      const meeting = res.data.data
      if (meeting.presenters && meeting.presenters.length > 0) {
        // 遍历每个汇报人，获取其材料
        for (const p of meeting.presenters) {
          const filesRes = await recordApi.getPresenterFiles(p.id)
          presenterMaterials.value.push({
            presenterId: p.id,
            presenterName: p.real_name || p.username,
            durationMinutes: p.duration_minutes,
            files: filesRes.data.files || []
          })
        }
      }
    }
  } catch (e) {
    console.error('加载材料失败:', e)
  }
  loading.value = false
}

async function downloadFile(fileId, filename) {
  try {
    const res = await recordApi.downloadFile(fileId)
    const blob = res.data
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    a.remove()
  } catch (e) {
    console.error('下载失败:', e)
    window.$toast?.('下载失败', 'error')
  }
}

onMounted(() => {
  loadMaterials()
})
</script>