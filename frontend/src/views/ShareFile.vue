<template>
  <div class="p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-800 mb-2">团队共享文件</h1>
      <p class="text-sm text-gray-500">管理非学术文件（PPT、Word、Excel、压缩包等），支持团队协作共享</p>
    </div>

    <!-- 操作栏 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div class="flex flex-col sm:flex-row gap-4 flex-1">
          <!-- 文件类型筛选 -->
          <select v-model="fileTypeFilter" class="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="">所有类型</option>
            <option value="pdf">PDF文档</option>
            <option value="doc">Word文档</option>
            <option value="ppt">PPT演示</option>
            <option value="xls">Excel表格</option>
            <option value="zip">压缩包</option>
            <option value="other">其他</option>
          </select>

          <!-- 时间排序 -->
          <select v-model="sortBy" @change="loadFiles" class="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <option value="newest">最新上传</option>
            <option value="oldest">最早上传</option>
            <option value="name">按名称</option>
            <option value="size">按大小</option>
          </select>

          <!-- 搜索框 -->
          <div class="relative">
            <input v-model="searchKeyword" type="text" class="w-full sm:w-48 lg:w-64 px-4 py-2 pl-10 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary" placeholder="搜索文件...">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <!-- 布局切换按钮组 -->
          <div class="bg-gray-100 rounded-lg p-1 flex">
            <button @click="setLayout('list')" :class="layoutBtnClass('list')" class="px-3 py-2 rounded-md text-sm font-medium transition-all duration-200" title="列表视图">
              <i class="fa fa-list"></i>
            </button>
            <button @click="setLayout('grid')" :class="layoutBtnClass('grid')" class="px-3 py-2 rounded-md text-sm font-medium transition-all duration-200" title="卡片视图">
              <i class="fa fa-th-large"></i>
            </button>
          </div>

          <!-- 上传按钮 -->
          <button @click="openUploadModal" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2">
            <i class="fa fa-upload"></i>
            <span>上传文件</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 文件统计 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">总文件数</p>
            <h3 class="text-2xl font-bold mt-1">{{ stats.total_files || 0 }}</h3>
          </div>
          <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            <i class="fa fa-file"></i>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">总大小</p>
            <h3 class="text-2xl font-bold mt-1">{{ formatFileSize(stats.total_size || 0) }}</h3>
          </div>
          <div class="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center text-secondary">
            <i class="fa fa-database"></i>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">本周新增</p>
            <h3 class="text-2xl font-bold mt-1">{{ stats.weekly_new || 0 }}</h3>
          </div>
          <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600">
            <i class="fa fa-plus"></i>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">共享者</p>
            <h3 class="text-2xl font-bold mt-1">{{ stats.sharers || 0 }}</h3>
          </div>
          <div class="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
            <i class="fa fa-users"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-show="currentLayout === 'list'" class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <!-- 表格头部 -->
      <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div class="grid grid-cols-12 gap-4 items-center text-xs font-medium text-gray-500 uppercase tracking-wider">
          <div class="col-span-6">文件信息</div>
          <div class="col-span-2 text-center">上传者</div>
          <div class="col-span-2 text-center">文件大小</div>
          <div class="col-span-2 text-center">操作</div>
        </div>
      </div>

      <!-- 表格内容 -->
      <div class="divide-y divide-gray-100">
        <div v-if="filteredFiles.length > 0">
          <div v-for="file in filteredFiles" :key="file.id" class="file-row px-6 py-4 hover:bg-gray-50 transition-colors">
            <div class="grid grid-cols-12 gap-4 items-center">
              <!-- 文件信息 -->
              <div class="col-span-6 flex items-center gap-4">
                <div :class="fileTypeClass(file.file_type)" class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <i :class="fileTypeIcon(file.file_type)" class="fa text-lg"></i>
                </div>
                <div class="min-w-0 flex-1">
                  <h3 class="font-medium text-gray-800 truncate" :title="file.filename">{{ file.filename }}</h3>
                  <p class="text-sm text-gray-500">{{ formatDate(file.upload_time) }}</p>
                  <p v-if="file.description" class="text-xs text-gray-400 line-clamp-1 mt-1">{{ file.description }}</p>
                </div>
              </div>

              <!-- 上传者 -->
              <div class="col-span-2 text-center">
                <div class="flex items-center justify-center gap-2">
                  <img :src="getAvatarUrl(file.uploader_id)" :alt="file.uploader_name" class="w-6 h-6 rounded-full">
                  <span class="text-sm text-gray-600">{{ file.uploader_name || '未知' }}</span>
                </div>
              </div>

              <!-- 文件大小 -->
              <div class="col-span-2 text-center">
                <span class="text-sm text-gray-600">{{ formatFileSize(file.file_size) }}</span>
              </div>

              <!-- 操作按钮 -->
              <div class="col-span-2 text-center">
                <div class="flex items-center justify-center gap-2">
                  <button @click="downloadFile(file.id, file.filename)" class="text-gray-400 hover:text-primary transition-colors p-2" title="下载">
                    <i class="fa fa-download"></i>
                  </button>
                  <button @click="previewFile(file.id)" class="text-gray-400 hover:text-secondary transition-colors p-2" title="预览">
                    <i class="fa fa-eye"></i>
                  </button>
                  <button @click="deleteFile(file.id, file.filename)" class="text-gray-400 hover:text-red-500 transition-colors p-2" title="删除">
                    <i class="fa fa-trash-o"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-12 text-gray-500">
          <i class="fa fa-folder-open-o text-4xl mb-3"></i><p>暂无文件</p>
        </div>
      </div>

      <!-- 分页控件 -->
      <div v-if="pagination.total > 0" class="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-600">每页显示</label>
              <select v-model="perPage" @change="changePerPage" class="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="5">5条</option>
                <option value="10">10条</option>
                <option value="20">20条</option>
                <option value="100">100条</option>
              </select>
            </div>
            <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ pagination.total }} 条</div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="prevPage" :disabled="!pagination.has_prev"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              <i class="fa fa-chevron-left mr-1"></i>上一页
            </button>
            <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
            <button @click="nextPage" :disabled="!pagination.has_next"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              下一页<i class="fa fa-chevron-right ml-1"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 网格视图 -->
    <div v-show="currentLayout === 'grid'">
      <div v-if="files.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div v-for="file in filteredFiles" :key="file.id" class="file-card bg-white rounded-xl shadow-sm border border-gray-100 p-4 transition-all duration-200 hover:shadow-md hover:-translate-y-1">
          <div class="flex items-start justify-between mb-3">
            <div :class="fileTypeClass(file.file_type)" class="w-12 h-12 rounded-lg flex items-center justify-center">
              <i :class="fileTypeIcon(file.file_type)" class="fa text-xl"></i>
            </div>
            <button @click="deleteFile(file.id, file.filename)" class="text-gray-400 hover:text-red-500 transition-colors">
              <i class="fa fa-trash-o"></i>
            </button>
          </div>
          <h3 class="font-medium text-gray-800 mb-1 line-clamp-2" :title="file.filename">{{ file.filename }}</h3>
          <p class="text-sm text-gray-500 mb-3">{{ file.uploader_name || '未知' }} · {{ formatDate(file.upload_time) }}</p>
          <p v-if="file.description" class="text-xs text-gray-400 mb-2 line-clamp-2">{{ file.description }}</p>
          <div class="flex items-center justify-between text-xs text-gray-400">
            <span>{{ formatFileSize(file.file_size) }}</span>
            <div class="flex items-center gap-2">
              <button @click="downloadFile(file.id, file.filename)" class="hover:text-primary transition-colors" title="下载">
                <i class="fa fa-download"></i>
              </button>
              <button @click="previewFile(file.id)" class="hover:text-secondary transition-colors" title="预览">
                <i class="fa fa-eye"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-12 text-gray-500">
        <i class="fa fa-folder-open-o text-4xl mb-3"></i><p>暂无文件</p>
      </div>

      <!-- 网格视图分页 -->
      <div v-if="pagination.total > 0" class="mt-6 px-4 py-3 bg-white rounded-lg border border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-600">每页显示</label>
              <select v-model="perPage" @change="changePerPage" class="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="5">5条</option>
                <option value="10">10条</option>
                <option value="20">20条</option>
                <option value="100">100条</option>
              </select>
            </div>
            <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ pagination.total }} 条</div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="prevPage" :disabled="!pagination.has_prev"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              <i class="fa fa-chevron-left mr-1"></i>上一页
            </button>
            <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
            <button @click="nextPage" :disabled="!pagination.has_next"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              下一页<i class="fa fa-chevron-right ml-1"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传文件模态框 -->
    <UploadFileModal
      v-model="uploadModalVisible"
      @uploaded="onFileUploaded"
      @close="uploadModalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/user'
import { fileApi } from '../api/share_file'
import UploadFileModal from '../components/UploadFileModal.vue'

const userStore = useUserStore()

// 文件数据
const files = ref([])
const stats = ref({
  total_files: 0,
  total_size: 0,
  weekly_new: 0,
  sharers: 0
})

// 分页
const currentPage = ref(1)
const perPage = ref(5)
const pagination = ref({
  total: 0,
  total_pages: 0,
  has_next: false,
  has_prev: false
})

// 筛选
const fileTypeFilter = ref('')
const sortBy = ref('newest')
const searchKeyword = ref('')

// 布局
const currentLayout = ref(localStorage.getItem('file_layout') || 'list')

// 模态框
const uploadModalVisible = ref(false)

// 计算属性
const startItem = computed(() => (currentPage.value - 1) * perPage.value + 1)
const endItem = computed(() => Math.min(currentPage.value * perPage.value, pagination.value.total))

// 加载文件统计
const loadStats = async () => {
  try {
    const res = await fileApi.getStats({ scope: 'public' })
    if (res.data.success) {
      stats.value = res.data.data
    }
  } catch (e) {
    console.error('加载文件统计失败:', e)
  }
}

// 加载文件列表
const loadFiles = async () => {
  try {
    const params = {
      scope: 'public',
      page: currentPage.value,
      limit: perPage.value,
      sort: sortBy.value
    }

    const res = await fileApi.getFiles(params)
    if (res.data.success) {
      files.value = res.data.data.files.map(file => ({
        ...file,
        simpleFileType: getFileTypeSimple(file.file_type)
      }))
      pagination.value = res.data.data.pagination
      stats.value.total_files = res.data.data.total_files_count || pagination.value.total
    }
  } catch (e) {
    console.error('加载文件列表失败:', e)
  }
}

// 获取简单文件类型（用于前端筛选）
const getFileTypeSimple = (fileType) => {
  if (!fileType) return 'other'
  if (fileType.includes('pdf')) return 'pdf'
  if (fileType.includes('word') || fileType.includes('document')) return 'doc'
  if (fileType.includes('powerpoint') || fileType.includes('presentation')) return 'ppt'
  if (fileType.includes('excel') || fileType.includes('sheet')) return 'xls'
  if (fileType.includes('zip') || fileType.includes('rar')) return 'zip'
  return 'other'
}

// 前端筛选后的文件列表
const filteredFiles = computed(() => {
  let result = files.value

  // 文件类型筛选
  if (fileTypeFilter.value) {
    result = result.filter(file => file.simpleFileType === fileTypeFilter.value)
  }

  // 搜索筛选
  if (searchKeyword.value) {
    const term = searchKeyword.value.toLowerCase()
    result = result.filter(file =>
      (file.filename?.toLowerCase().includes(term)) ||
      (file.description?.toLowerCase().includes(term)) ||
      (file.uploader_name?.toLowerCase().includes(term))
    )
  }

  return result
})

// 布局切换
const setLayout = (layout) => {
  currentLayout.value = layout
  localStorage.setItem('file_layout', layout)
}

const layoutBtnClass = (layout) => {
  if (currentLayout.value === layout) {
    return 'bg-white text-gray-900 shadow-sm'
  }
  return 'text-gray-500 hover:text-gray-700'
}

// 分页操作
const prevPage = () => {
  if (pagination.value.has_prev) {
    currentPage.value--
    loadFiles()
  }
}

const nextPage = () => {
  if (pagination.value.has_next) {
    currentPage.value++
    loadFiles()
  }
}

const changePerPage = () => {
  currentPage.value = 1
  loadFiles()
}

// 文件操作
const downloadFile = async (fileId, filename) => {
  try {
    await fileApi.downloadFile(fileId, filename)
    showToast(`开始下载 ${filename}`, 'success')
  } catch (e) {
    console.error('下载失败:', e)
    showToast('下载失败，请重试', 'error')
  }
}

const previewFile = (fileId) => {
  const token = localStorage.getItem('session_token')
  const baseUrl = axios.defaults.baseURL || window.location.origin
  const url = `${baseUrl}/api/files/${fileId}/view${token ? `?session_token=${token}` : ''}`
  window.open(url, '_blank')
}

const deleteFile = async (fileId, filename) => {
  if (!confirm(`确定要删除文件 "${filename}" 吗？此操作不可撤销。`)) {
    return
  }

  try {
    const res = await fileApi.deleteFile(fileId)
    if (res.data.success) {
      showToast(`文件 "${filename}" 已删除`, 'success')
      loadStats()
      loadFiles()
    } else {
      showToast(res.data.message || '删除失败', 'error')
    }
  } catch (e) {
    console.error('删除失败:', e)
    showToast('删除失败，请重试', 'error')
  }
}

// 模态框
const openUploadModal = () => {
  uploadModalVisible.value = true
}

const onFileUploaded = () => {
  loadStats()
  loadFiles()
}

// 辅助函数
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
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
  if (fileType.includes('image')) return 'bg-pink-50 text-pink-500'
  return 'bg-gray-50 text-gray-500'
}

const fileTypeIcon = (fileType) => {
  if (!fileType) return 'fa-file-o'
  if (fileType.includes('pdf')) return 'fa-file-pdf-o'
  if (fileType.includes('word') || fileType.includes('document')) return 'fa-file-word-o'
  if (fileType.includes('powerpoint') || fileType.includes('presentation')) return 'fa-file-powerpoint-o'
  if (fileType.includes('excel') || fileType.includes('sheet')) return 'fa-file-excel-o'
  if (fileType.includes('zip') || fileType.includes('rar')) return 'fa-file-archive-o'
  if (fileType.includes('image')) return 'fa-file-image-o'
  return 'fa-file-o'
}

const getAvatarUrl = (uploaderId) => {
  if (!uploaderId) return 'https://ui-avatars.com/api/?name=U&background=2563eb&color=fff&size=128'
  return `https://picsum.photos/id/${uploaderId}/200/200`
}

// Toast提示
const showToast = (message, type = 'info') => {
  const toastDiv = document.createElement('div')
  const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-primary'
  toastDiv.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-3 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300`
  toastDiv.innerHTML = `<div class="flex items-center"><i class="fa ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle'} mr-2"></i><span>${message}</span></div>`
  document.body.appendChild(toastDiv)

  setTimeout(() => toastDiv.classList.remove('translate-x-full'), 100)
  setTimeout(() => {
    toastDiv.classList.add('translate-x-full')
    setTimeout(() => toastDiv.remove(), 300)
  }, 3000)
}

// 初始化
onMounted(() => {
  loadStats()
  loadFiles()
})
</script>

<style scoped>
.file-row {
  transition: all 0.2s;
}
.file-row:hover {
  background-color: #f9fafb;
}
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>