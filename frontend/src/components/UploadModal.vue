<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-md w-full mx-4 overflow-hidden">
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <h2 class="text-lg font-bold text-gray-800">上传汇报材料</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>
      <div class="p-6">
        <div class="mb-4 p-3 bg-gray-50 rounded-lg text-sm">
          <p><strong>组会：</strong>{{ meetingTitle }}</p>
          <p><strong>汇报人：</strong>{{ presenterName }}</p>
        </div>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">选择文件</label>
          <input type="file" ref="fileInput" accept=".pdf,.ppt,.pptx,.doc,.docx,.xls,.xlsx" class="w-full px-3 py-2 border rounded-lg">
          <p class="text-xs text-gray-500 mt-1">支持 PDF、PPT、DOC、XLS 格式，单个文件最大50MB</p>
        </div>
        <!-- 已上传文件列表 -->
        <div v-if="existingFiles.length > 0" class="mb-4">
          <p class="text-sm font-medium text-gray-700 mb-2">已上传文件</p>
          <div class="space-y-2">
            <div v-for="f in existingFiles" :key="f.id" class="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span class="text-sm text-gray-700"><i class="fa fa-file-o mr-1 text-gray-400"></i>{{ f.filename }}</span>
              <div class="flex gap-2">
                <button @click="downloadFile(f.id, f.filename)" class="text-xs text-primary hover:underline">
                  <i class="fa fa-download"></i>
                </button>
                <button @click="deleteFile(f.id)" class="text-xs text-red-500 hover:underline">
                  <i class="fa fa-trash-o"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="px-6 py-4 border-t flex justify-end gap-3">
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">取消</button>
        <button @click="submitUpload" :disabled="uploading" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50">
          <i :class="uploading ? 'fa fa-spinner fa-spin' : 'fa fa-upload'" class="mr-1"></i>上传
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { materialApi } from '../api/material'

const props = defineProps({
  presenterId: Number,
  meetingId: Number,
  presenterName: String,
  meetingTitle: String
})

const emit = defineEmits(['close', 'success'])

const fileInput = ref(null)
const existingFiles = ref([])
const uploading = ref(false)

async function loadExistingFiles() {
  try {
    const res = await materialApi.getFiles(props.presenterId)
    if (res.data.success && res.data.files) {
      existingFiles.value = res.data.files
    }
  } catch (e) {
    console.error('加载文件失败:', e)
  }
}

async function submitUpload() {
  const file = fileInput.value?.files?.[0]
  if (!file) {
    window.$toast?.('请选择文件', 'warning')
    return
  }
  if (file.size > 50 * 1024 * 1024) {
    window.$toast?.('文件大小不能超过50MB', 'warning')
    return
  }

  uploading.value = true
  try {
    const res = await materialApi.uploadFile(props.presenterId, props.meetingId, file)
    if (res.data.success) {
      window.$toast?.('上传成功', 'success')
      emit('success')
    } else {
      window.$toast?.(res.data.message || '上传失败', 'error')
    }
  } catch (e) {
    console.error('上传失败:', e)
    window.$toast?.('网络错误', 'error')
  }
  uploading.value = false
}

async function downloadFile(fileId, filename) {
  try {
    const res = await materialApi.downloadFile(fileId)
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

async function deleteFile(fileId) {
  try {
    const res = await materialApi.deleteFile(fileId)
    if (res.data.success) {
      window.$toast?.('文件已删除', 'success')
      loadExistingFiles()
    } else {
      window.$toast?.(res.data.message || '删除失败', 'error')
    }
  } catch (e) {
    console.error('删除失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

onMounted(() => {
  loadExistingFiles()
})
</script>