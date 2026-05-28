<template>
  <div v-if="visible" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
    <div class="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
      <!-- 模态框头部 -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-800">上传文件</h3>
        <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>

      <!-- 模态框内容 -->
      <div class="p-6">
        <!-- 文件拖拽区域 -->
        <div
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
          :class="dropZoneClass"
          class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center transition-colors">
          <i class="fa fa-cloud-upload text-4xl text-gray-400 mb-4"></i>
          <p class="text-gray-600 mb-2">拖拽文件到此处上传</p>
          <p class="text-sm text-gray-500 mb-4">或者</p>
          <label for="file-upload-input" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors cursor-pointer inline-block">
            <i class="fa fa-folder-open mr-2"></i>选择文件
          </label>
          <input id="file-upload-input" ref="fileInput" type="file" @change="onFileSelect" class="hidden" multiple accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt,.md,.jpg,.jpeg,.png,.gif">
          <p class="text-xs text-gray-500 mt-4">支持格式：PDF、Word、PPT、Excel、压缩包、文本文件等</p>
          <p class="text-xs text-gray-500">单个文件最大 50MB，总大小最大 200MB</p>
        </div>

        <!-- 文件列表 -->
        <div v-if="selectedFiles.length > 0" class="mt-6">
          <h4 class="font-medium text-gray-700 mb-3">待上传文件</h4>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div v-for="(file, index) in selectedFiles" :key="index" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div class="flex items-center gap-3">
                <div :class="fileTypeClass(file.type)" class="w-10 h-10 rounded-lg flex items-center justify-center">
                  <i :class="fileTypeIcon(file.type)" class="fa text-xl"></i>
                </div>
                <div>
                  <p class="font-medium text-gray-800 text-sm line-clamp-1">{{ file.name }}</p>
                  <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
                </div>
              </div>
              <button @click="removeFile(index)" class="text-red-500 hover:text-red-700">
                <i class="fa fa-times"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 上传设置 -->
        <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文件分类</label>
            <select v-model="category" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="">选择分类</option>
              <option value="research">研究资料</option>
              <option value="report">汇报材料</option>
              <option value="paper">学术论文</option>
              <option value="data">实验数据</option>
              <option value="code">代码文件</option>
              <option value="other">其他文件</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">访问权限</label>
            <select v-model="permission" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="public">所有人可见</option>
              <option value="team">团队成员可见</option>
              <option value="private">仅自己可见</option>
            </select>
          </div>
        </div>

        <!-- 文件描述 -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">文件描述</label>
          <textarea v-model="description" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none" placeholder="请输入文件描述（可选）"></textarea>
        </div>

        <!-- 上传进度 -->
        <div v-if="uploading" class="mt-4">
          <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>{{ uploadMessage }}</span>
            <span>{{ uploadProgress }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-primary h-2 rounded-full transition-all" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- 模态框底部 -->
      <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
        <button @click="close" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors">
          取消
        </button>
        <button @click="startUpload" :disabled="selectedFiles.length === 0 || uploading || !category"
                class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          <i class="fa fa-upload mr-2"></i>开始上传
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { fileApi } from '../api/share_file'

const visible = defineModel()
const emit = defineEmits(['uploaded', 'close'])

const selectedFiles = ref([])
const category = ref('paper')
const permission = ref('public')
const description = ref('')
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadMessage = ref('')
const isDragOver = ref(false)
const fileInput = ref(null)

const maxFileSize = 50 * 1024 * 1024 // 50MB
const maxTotalSize = 200 * 1024 * 1024 // 200MB

const dropZoneClass = computed(() => {
  return isDragOver.value ? 'border-primary bg-primary/5' : ''
})

const onDragOver = () => {
  isDragOver.value = true
}

const onDragLeave = () => {
  isDragOver.value = false
}

const onDrop = (e) => {
  isDragOver.value = false
  handleFiles(e.dataTransfer.files)
}

const onFileSelect = (e) => {
  handleFiles(e.target.files)
}

const handleFiles = (files) => {
  let totalSize = selectedFiles.value.reduce((sum, f) => sum + f.size, 0)

  Array.from(files).forEach(file => {
    if (file.size > maxFileSize) {
      alert(`文件 ${file.name} 超过大小限制 (50MB)`)
      return
    }

    if (totalSize + file.size > maxTotalSize) {
      alert('文件总大小超过限制 (200MB)')
      return
    }

    if (!selectedFiles.value.find(f => f.name === file.name && f.size === file.size)) {
      selectedFiles.value.push(file)
      totalSize += file.size
    }
  })
}

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
}

const startUpload = async () => {
  if (selectedFiles.value.length === 0 || !category.value) return

  uploading.value = true
  uploadProgress.value = 0
  let successCount = 0

  for (let i = 0; i < selectedFiles.value.length; i++) {
    const file = selectedFiles.value[i]
    uploadMessage.value = `正在上传 ${file.name} (${i + 1}/${selectedFiles.value.length})`
    uploadProgress.value = Math.round(((i + 1) / selectedFiles.value.length) * 100)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('description', description.value)
      formData.append('tags', category.value)
      formData.append('is_public', permission.value === 'public' ? 'true' : 'false')

      const res = await fileApi.uploadFile(formData)
      if (res.data.success) {
        successCount++
      } else {
        alert(`文件 ${file.name} 上传失败: ${res.data.message}`)
      }
    } catch (e) {
      console.error('上传失败:', e)
      alert(`文件 ${file.name} 上传失败`)
    }
  }

  uploading.value = false

  if (successCount > 0) {
    emit('uploaded')
    close()
  }
}

const close = () => {
  visible.value = false
  selectedFiles.value = []
  category.value = 'paper'
  permission.value = 'public'
  description.value = ''
  uploadProgress.value = 0
  uploadMessage.value = ''
  emit('close')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const fileTypeClass = (fileType) => {
  if (!fileType) return 'bg-gray-50 text-gray-500'
  if (fileType.includes('pdf')) return 'bg-red-50 text-red-500'
  if (fileType.includes('word') || fileType.includes('document')) return 'bg-blue-50 text-blue-500'
  if (fileType.includes('powerpoint') || fileType.includes('presentation')) return 'bg-orange-50 text-orange-500'
  if (fileType.includes('excel') || fileType.includes('sheet')) return 'bg-green-50 text-green-500'
  if (fileType.includes('zip') || fileType.includes('rar')) return 'bg-purple-50 text-purple-500'
  return 'bg-gray-50 text-gray-500'
}

const fileTypeIcon = (fileType) => {
  if (!fileType) return 'fa-file-o'
  if (fileType.includes('pdf')) return 'fa-file-pdf-o'
  if (fileType.includes('word') || fileType.includes('document')) return 'fa-file-word-o'
  if (fileType.includes('powerpoint') || fileType.includes('presentation')) return 'fa-file-powerpoint-o'
  if (fileType.includes('excel') || fileType.includes('sheet')) return 'fa-file-excel-o'
  if (fileType.includes('zip') || fileType.includes('rar')) return 'fa-file-archive-o'
  return 'fa-file-o'
}
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>