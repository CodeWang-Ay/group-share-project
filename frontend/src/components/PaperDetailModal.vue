<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
      <!-- 模态框头部 -->
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 class="font-semibold text-gray-800">文献详情</h3>
        <button @click="close" class="p-2 hover:bg-gray-100 rounded-lg">
          <i class="fa fa-times text-gray-500"></i>
        </button>
      </div>

      <!-- 内容区 -->
      <div class="p-6 overflow-y-auto">
        <!-- 标题和收藏 -->
        <div class="flex items-start gap-3 mb-4">
          <div class="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center">
            <i class="fa fa-file-pdf-o text-blue-500 text-2xl"></i>
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-gray-800">{{ paper?.title }}</h2>
            <div class="flex items-center gap-3 mt-2">
              <button @click="toggleStar" :class="paper?.is_starred ? 'text-yellow-500' : 'text-gray-400'" class="text-lg">
                {{ paper?.is_starred ? '⭐' : '☆' }}
                {{ paper?.is_starred ? '已收藏' : '未收藏' }}
              </button>
              <span :class="statusClass" class="px-2 py-1 rounded-full text-xs">{{ statusText }}</span>
            </div>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="bg-gray-50 rounded-lg p-3">
            <p class="text-sm text-gray-500 mb-1">作者</p>
            <p class="font-medium">{{ paper?.authors || '无' }}</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-3">
            <p class="text-sm text-gray-500 mb-1">发表年份</p>
            <p class="font-medium">{{ paper?.year || '无' }}</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-3">
            <p class="text-sm text-gray-500 mb-1">期刊/会议</p>
            <p class="font-medium">{{ paper?.journal || '无' }}</p>
          </div>
          <div class="bg-gray-50 rounded-lg p-3">
            <p class="text-sm text-gray-500 mb-1">DOI</p>
            <p class="font-medium text-primary cursor-pointer hover:underline">{{ paper?.doi || '无' }}</p>
          </div>
        </div>

        <!-- 标签 -->
        <div class="mb-6">
          <p class="text-sm text-gray-500 mb-2">标签</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="tag in paper?.tags || []" :key="tag.name"
                  class="tag-badge bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs font-medium">
              {{ tag.name }}
            </span>
          </div>
        </div>

        <!-- 摘要 -->
        <div class="mb-6">
          <p class="text-sm text-gray-500 mb-2">摘要</p>
          <div class="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 leading-relaxed">
            <p>{{ paper?.abstract || '无摘要' }}</p>
          </div>
        </div>

        <!-- 链接和文件 -->
        <div class="mb-6">
          <p class="text-sm text-gray-500 mb-2">相关链接</p>
          <div class="flex flex-wrap gap-3">
            <a :href="pdfDownloadUrl" target="_blank"
               class="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors">
              <i class="fa fa-file-pdf-o"></i> PDF全文
            </a>
            <a v-if="paper?.arxiv_link" :href="paper.arxiv_link" target="_blank"
               class="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
              <i class="fa fa-external-link"></i> arXiv
            </a>
            <a v-if="paper?.semantic_scholar_link" :href="paper.semantic_scholar_link" target="_blank"
               class="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors">
              <i class="fa fa-graduation-cap"></i> Semantic Scholar
            </a>
          </div>
        </div>

        <!-- 添加者信息 -->
        <div class="bg-gray-50 rounded-lg p-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <img :src="paper?.uploader_avatar || `https://picsum.photos/id/${paper?.uploader_id || 1}/100/100`"
                   class="w-6 h-6 rounded-full">
              <span class="text-sm text-gray-600">
                由 <span class="font-medium">{{ paper?.uploader_name || '未知' }}</span> 添加于
                <span>{{ formatTime(paper?.created_at) }}</span>
              </span>
            </div>
            <div class="text-sm text-gray-500">
              <span>下载 {{ paper?.download_count || 0 }} 次</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作区 -->
      <div class="p-4 border-t border-gray-200 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <select v-model="readStatus" @change="updateReadStatus"
                  class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30">
            <option value="unread">未读</option>
            <option value="reading">在读</option>
            <option value="read">已读</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <button @click="editPaper" class="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <i class="fa fa-edit mr-1"></i>编辑
          </button>
          <button @click="downloadPaper" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
            <i class="fa fa-download mr-1"></i>下载PDF
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { paperApi } from '../api/paper'

const visible = defineModel()
const props = defineProps({
  paper: Object,
  libraryType: String
})

const emit = defineEmits(['update', 'edit', 'close'])

const readStatus = ref('unread')

// 监听 paper 变化更新阅读状态
watch(() => props.paper, (newPaper) => {
  if (newPaper) {
    readStatus.value = newPaper.read_status || 'unread'
  }
})

const statusClass = computed(() => {
  const map = {
    unread: 'bg-gray-100 text-gray-700',
    reading: 'bg-yellow-100 text-yellow-700',
    read: 'bg-green-100 text-green-700'
  }
  return map[props.paper?.read_status] || 'bg-gray-100 text-gray-700'
})

const statusText = computed(() => {
  const map = {
    unread: '未读',
    reading: '在读',
    read: '已读'
  }
  return map[props.paper?.read_status] || '未读'
})

const pdfDownloadUrl = computed(() => {
  if (!props.paper?.id) return '#'
  return paperApi.getDownloadUrl(props.paper.id, props.libraryType)
})

const formatTime = (time) => {
  if (!time) return '未知'
  return time.split('.')[0].replace('T', ' ')
}

const close = () => {
  visible.value = false
  emit('close')
}

const toggleStar = async () => {
  if (!props.paper?.id) return
  try {
    const res = await paperApi.toggleStar(props.paper.id, props.libraryType)
    if (res.data.success) {
      emit('update')
    }
  } catch (e) {
    console.error('收藏失败:', e)
  }
}

const updateReadStatus = async () => {
  if (!props.paper?.id) return
  try {
    const res = await paperApi.updateStatus(props.paper.id, readStatus.value, props.libraryType)
    if (res.data.success) {
      emit('update')
      close()
    }
  } catch (e) {
    console.error('更新状态失败:', e)
  }
}

const editPaper = () => {
  emit('edit', props.paper?.id)
  close()
}

const downloadPaper = () => {
  if (props.paper?.id) {
    paperApi.downloadPaper(props.paper.id, props.libraryType)
  }
}
</script>

<style scoped>
.tag-badge {
  transition-colors: ease-in-out 0.15s;
}
</style>