<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
      <!-- 模态框头部 -->
      <div class="p-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
        <h3 class="font-semibold text-gray-800">{{ isEdit ? '编辑文献' : '添加文献' }}</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <!-- 表单内容 -->
      <div class="p-6 overflow-y-auto flex-1 space-y-4">
        <!-- 标题 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">标题 *</label>
          <input v-model="form.title" type="text"
                 class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
        </div>

        <!-- 作者 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">作者</label>
          <input v-model="form.authors" type="text" placeholder="多个作者用逗号分隔"
                 class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
        </div>

        <!-- 年份和期刊 -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">发表年份</label>
            <input v-model="form.year" type="number"
                   class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">期刊/会议</label>
            <input v-model="form.journal" type="text"
                   class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
          </div>
        </div>

        <!-- 标签 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">标签</label>
          <input v-model="form.tags" type="text" placeholder="多个标签用逗号分隔"
                 class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
          <div class="flex flex-wrap gap-2 mt-2">
            <span v-for="tag in quickTags" :key="tag"
                  @click="addTag(tag)"
                  class="tag-badge cursor-pointer px-2 py-1 rounded text-xs font-medium"
                  :class="getTagClass(tag)">
              + {{ tag }}
            </span>
          </div>
        </div>

        <!-- 存储位置 (仅添加模式) -->
        <div v-if="!isEdit">
          <label class="block text-sm font-medium text-gray-700 mb-1">存储位置</label>
          <select v-model="form.library_type"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="public">团队文献库（所有人可见）</option>
            <option value="private">我的文献库（仅自己可见）</option>
          </select>
        </div>

        <!-- 阅读状态 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">阅读状态</label>
          <select v-model="form.read_status"
                  class="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="unread">未读</option>
            <option value="reading">在读</option>
            <option value="read">已读</option>
          </select>
        </div>

        <!-- PDF文件上传 (仅添加模式) -->
        <div v-if="!isEdit">
          <label class="block text-sm font-medium text-gray-700 mb-1">PDF文件</label>
          <div
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
            @click="triggerFileSelect"
            :class="['border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer',
                     isDragOver ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50']">
            <i class="fa fa-cloud-upload text-3xl text-gray-400 mb-3"></i>
            <p class="text-gray-600 mb-1">拖拽PDF文件到此处上传</p>
            <p class="text-sm text-gray-500 mb-3">或者</p>
            <button class="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <i class="fa fa-folder-open mr-1"></i>选择文件
            </button>
            <input ref="fileInput" type="file" accept=".pdf" @change="onFileSelect" class="hidden">
            <p class="text-xs text-gray-500 mt-3">仅支持PDF格式，最大50MB</p>
          </div>
          <!-- 已选文件显示 -->
          <div v-if="selectedFile" class="mt-3">
            <div class="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div class="flex items-center gap-2">
                <i class="fa fa-file-pdf-o text-red-500"></i>
                <span class="text-sm text-gray-700">{{ selectedFile.name }}</span>
                <span class="text-xs text-gray-500">({{ formatFileSize(selectedFile.size) }})</span>
              </div>
              <button @click="removeFile" class="text-red-500 hover:text-red-700">
                <i class="fa fa-times"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 已有文件显示 (编辑模式) -->
        <div v-if="isEdit && existingFileName">
          <label class="block text-sm font-medium text-gray-700 mb-1">PDF文件</label>
          <div class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
            <i class="fa fa-file-pdf-o text-red-500"></i>
            <span class="text-sm text-gray-700">已有文件: {{ existingFileName }}</span>
          </div>
        </div>

        <!-- 外部链接 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">外部链接</label>
          <div class="grid grid-cols-2 gap-4">
            <input v-model="form.arxiv_link" type="text" placeholder="arXiv链接"
                   class="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <input v-model="form.semantic_scholar_link" type="text" placeholder="Semantic Scholar链接"
                   class="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="p-4 border-t border-gray-200 flex items-center justify-end gap-3 flex-shrink-0 bg-white">
        <button @click="close" class="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
          取消
        </button>
        <button @click="save" :disabled="saving"
                class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50">
          <i class="fa fa-check mr-1"></i>保存
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { paperApi } from '../api/paper'

const visible = defineModel()
const props = defineProps({
  paperId: Number,
  libraryType: String
})

const emit = defineEmits(['saved', 'close'])

const isEdit = computed(() => props.paperId != null)

const form = ref({
  title: '',
  authors: '',
  year: '',
  journal: '',
  tags: '',
  library_type: 'public',
  read_status: 'unread',
  arxiv_link: '',
  semantic_scholar_link: ''
})

const selectedFile = ref(null)
const existingFileName = ref('')
const isDragOver = ref(false)
const saving = ref(false)
const fileInput = ref(null)

const quickTags = ['Transformer', 'BERT', 'CNN', '大模型', 'NLP', '计算机视觉']

const getTagClass = (tag) => {
  const classes = {
    'Transformer': 'bg-blue-100 text-blue-700',
    'BERT': 'bg-purple-100 text-purple-700',
    'CNN': 'bg-orange-100 text-orange-700',
    '大模型': 'bg-red-100 text-red-700',
    'NLP': 'bg-green-100 text-green-700',
    '计算机视觉': 'bg-gray-100 text-gray-700'
  }
  return classes[tag] || 'bg-gray-100 text-gray-700'
}

const addTag = (tag) => {
  const currentTags = form.value.tags.split(',').map(t => t.trim()).filter(t => t)
  if (!currentTags.includes(tag)) {
    currentTags.push(tag)
    form.value.tags = currentTags.join(', ')
  }
}

// 监听 paperId 变化，加载文献详情
watch(() => props.paperId, async (newId) => {
  if (newId && visible.value) {
    try {
      const res = await paperApi.getPaperDetail(newId, props.libraryType)
      if (res.data.success) {
        const paper = res.data.data
        form.value.title = paper.title || ''
        form.value.authors = paper.authors || ''
        form.value.year = paper.year || ''
        form.value.journal = paper.journal || ''
        form.value.tags = (paper.tags || []).map(t => t.name).join(', ')
        form.value.read_status = paper.read_status || 'unread'
        form.value.arxiv_link = paper.arxiv_link || ''
        form.value.semantic_scholar_link = paper.semantic_scholar_link || ''
        // 提取已有文件名
        if (paper.pdf_path) {
          existingFileName.value = paper.pdf_path.split('/').pop().replace(/^\d+_/, '')
        }
      }
    } catch (e) {
      console.error('加载文献详情失败:', e)
    }
  }
})

// 监听 visible 变化，重置表单
watch(visible, (val) => {
  if (val && !props.paperId) {
    resetForm()
    form.value.library_type = props.libraryType || 'public'
  }
})

const resetForm = () => {
  form.value = {
    title: '',
    authors: '',
    year: '',
    journal: '',
    tags: '',
    library_type: 'public',
    read_status: 'unread',
    arxiv_link: '',
    semantic_scholar_link: ''
  }
  selectedFile.value = null
  existingFileName.value = ''
}

const onDragOver = () => {
  isDragOver.value = true
}

const onDragLeave = () => {
  isDragOver.value = false
}

const onDrop = (e) => {
  isDragOver.value = false
  const files = e.dataTransfer.files
  if (files.length > 0) {
    handleFile(files[0])
  }
}

const triggerFileSelect = () => {
  fileInput.value?.click()
}

const onFileSelect = (e) => {
  if (e.target.files.length > 0) {
    handleFile(e.target.files[0])
  }
}

const handleFile = (file) => {
  if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
    alert('仅支持PDF格式文件')
    return
  }
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    alert('文件大小超过50MB限制')
    return
  }
  selectedFile.value = file
}

const removeFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const save = async () => {
  if (!form.value.title) {
    alert('请填写文献标题')
    return
  }

  if (!isEdit.value && !selectedFile.value) {
    alert('请上传PDF文件')
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      // 编辑模式：PUT 更新元数据
      const res = await paperApi.updatePaper(props.paperId, {
        title: form.value.title,
        authors: form.value.authors,
        year: form.value.year,
        journal: form.value.journal,
        tags: form.value.tags,
        read_status: form.value.read_status,
        arxiv_link: form.value.arxiv_link,
        semantic_scholar_link: form.value.semantic_scholar_link,
        library_type: props.libraryType
      })
      if (res.data.success) {
        emit('saved')
        close()
      } else {
        alert(res.data.message || '更新失败')
      }
    } else {
      // 添加模式：POST 上传新文献
      const formData = new FormData()
      formData.append('title', form.value.title)
      formData.append('authors', form.value.authors)
      formData.append('year', form.value.year)
      formData.append('journal', form.value.journal)
      formData.append('tags', form.value.tags)
      formData.append('library_type', form.value.library_type)
      formData.append('pdf', selectedFile.value)
      if (form.value.arxiv_link) formData.append('arxiv_link', form.value.arxiv_link)
      if (form.value.semantic_scholar_link) formData.append('semantic_scholar_link', form.value.semantic_scholar_link)

      const res = await paperApi.uploadPaper(formData)
      if (res.data.success) {
        emit('saved')
        close()
      } else {
        alert(res.data.message || '添加失败')
      }
    }
  } catch (e) {
    console.error('保存失败:', e)
    alert('保存失败')
  } finally {
    saving.value = false
  }
}

const close = () => {
  visible.value = false
  emit('close')
}
</script>

<style scoped>
.tag-badge {
  transition-colors: ease-in-out 0.15s;
}
.tag-badge:hover {
  opacity: 80;
}
</style>