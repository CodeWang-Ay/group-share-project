<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-lg w-full mx-4 overflow-hidden">
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <div>
          <h2 class="text-lg font-bold text-gray-800">汇报材料</h2>
          <p class="text-sm text-gray-500">{{ meetingTitle }}</p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>
      <div class="p-6">
        <div v-if="loading" class="text-center py-4 text-gray-500"><i class="fa fa-spinner fa-spin"></i> 加载中...</div>
        <div v-else-if="materials.length === 0" class="text-center py-4 text-gray-500">暂无汇报材料</div>
        <div v-else class="space-y-2">
          <div v-for="f in materials" :key="f.id" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100">
            <div class="flex items-center gap-3">
              <div :class="fileIconClass(f.file_type)" class="w-10 h-10 rounded-lg flex items-center justify-center">
                <i class="fa fa-file-o"></i>
              </div>
              <div>
                <p class="font-medium text-gray-800">{{ f.filename }}</p>
                <p class="text-xs text-gray-500">{{ formatSize(f.file_size) }}</p>
              </div>
            </div>
            <button @click="downloadFile(f.id, f.filename)" class="px-3 py-1 bg-primary text-white text-sm rounded-lg hover:bg-primary/90">
              <i class="fa fa-download"></i> 下载
            </button>
          </div>
        </div>
      </div>
      <div class="px-6 py-4 border-t flex justify-end">
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { recordApi } from '../api/record'

const props = defineProps({
  meetingId: Number,
  meetingTitle: String
})

defineEmits(['close'])

const loading = ref(true)
const materials = ref([])

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

async function loadMaterials() {
  loading.value = true
  materials.value = []
  try {
    const res = await recordApi.getMeetingDetail(props.meetingId)
    if (res.data.success) {
      const meeting = res.data.data
      if (meeting.presenters) {
        for (const p of meeting.presenters) {
          const filesRes = await recordApi.getPresenterFiles(p.id)
          if (filesRes.data.files) {
            materials.value.push(...filesRes.data.files)
          }
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