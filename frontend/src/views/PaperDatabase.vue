<template>
  <div class="p-6">
    <!-- 页面标题 -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-gray-800 mb-2">{{ libraryTitle }}</h1>
        <p class="text-sm text-gray-500">{{ libraryDesc }}</p>
      </div>
      <div class="flex gap-2">
        <button @click="switchLibrary('public')" :class="libraryBtnClass('public')" class="px-4 py-2 rounded-lg text-sm transition-colors">
          <i class="fa fa-users mr-1"></i>团队文献库
        </button>
        <button @click="switchLibrary('private')" :class="libraryBtnClass('private')" class="px-4 py-2 rounded-lg text-sm transition-colors">
          <i class="fa fa-user mr-1"></i>我的文献库
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">文献总数</p>
            <p class="text-2xl font-bold text-gray-800 mt-1">{{ stats.total || 0 }}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
            <i class="fa fa-book text-primary text-xl"></i>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">未读文献</p>
            <p class="text-2xl font-bold text-yellow-600 mt-1">{{ stats.unread || 0 }}</p>
          </div>
          <div class="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
            <i class="fa fa-eye-slash text-yellow-600 text-xl"></i>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">已收藏</p>
            <p class="text-2xl font-bold text-purple-600 mt-1">{{ stats.starred || 0 }}</p>
          </div>
          <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
            <i class="fa fa-star text-purple-600 text-xl"></i>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">近30天新增</p>
            <p class="text-2xl font-bold text-green-600 mt-1">{{ stats.recent || 0 }}</p>
          </div>
          <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
            <i class="fa fa-calendar-plus-o text-green-600 text-xl"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选区 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-4 mb-6">
      <div class="flex flex-col lg:flex-row gap-4">
        <!-- 搜索框 -->
        <div class="flex-1">
          <div class="relative">
            <input v-model="keyword" type="text" @input="onSearch" placeholder="搜索文献标题、作者、关键词..."
                   class="w-full py-2 pl-10 pr-4 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
          </div>
        </div>

        <!-- 筛选下拉 -->
        <div class="flex flex-wrap gap-3">
          <select v-model="currentTag" @change="loadPapers" class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30">
            <option value="">全部标签</option>
            <option v-for="tag in tags" :key="tag.name" :value="tag.name">{{ tag.name }}</option>
          </select>
          <select v-model="currentStatus" @change="loadPapers" class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30">
            <option value="">全部状态</option>
            <option value="unread">未读</option>
            <option value="reading">在读</option>
            <option value="read">已读</option>
          </select>
          <select v-model="currentStarred" @change="loadPapers" class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30">
            <option value="">全部收藏</option>
            <option value="starred">已收藏</option>
            <option value="unstarred">未收藏</option>
          </select>
          <button @click="clearFilters" class="px-3 py-2 text-sm text-gray-500 hover:text-primary transition-colors">
            <i class="fa fa-times mr-1"></i>清除筛选
          </button>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectMode" class="bg-primary/10 rounded-lg p-3 mb-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-sm text-primary">
          <i class="fa fa-check-square mr-1"></i>
          已选择 {{ selectedPapers.length }} 篇文献
        </span>
        <button @click="selectAll" class="text-sm text-gray-600 hover:text-primary">全选</button>
        <button @click="cancelSelection" class="text-sm text-gray-600 hover:text-primary">取消选择</button>
      </div>
      <div class="flex items-center gap-2">
        <button @click="batchStar(true)" class="px-3 py-1 bg-white border border-gray-200 rounded text-sm hover:bg-yellow-50 hover:border-yellow-300 transition-colors">
          ⭐ 批量收藏
        </button>
        <button @click="batchStar(false)" class="px-3 py-1 bg-white border border-gray-200 rounded text-sm hover:bg-gray-50 transition-colors">
          ☆ 取消收藏
        </button>
        <button @click="openBatchTagModal" class="px-3 py-1 bg-white border border-gray-200 rounded text-sm hover:bg-blue-50 hover:border-blue-300 transition-colors">
          <i class="fa fa-tag text-blue-500 mr-1"></i>设置标签
        </button>
        <button @click="batchDelete" class="px-3 py-1 bg-white border border-red-200 rounded text-sm text-red-600 hover:bg-red-50 transition-colors">
          <i class="fa fa-trash-o mr-1"></i>批量删除
        </button>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <button @click="toggleSelectMode" :class="selectMode ? 'bg-red-50 text-red-600 border-red-200' : ''" class="px-3 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors">
          <i :class="selectMode ? 'fa-times' : 'fa-check-square-o'" class="mr-1"></i>{{ selectMode ? '退出选择' : '批量选择' }}
        </button>
        <button @click="openAddModal" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
          <i class="fa fa-plus mr-1"></i>添加文献
        </button>
      </div>
      <div class="flex items-center gap-2">
        <select v-model="sortBy" @change="loadPapers" class="px-3 py-2 border border-gray-200 rounded-lg text-sm">
          <option value="newest">最新发表</option>
          <option value="oldest">最早发表</option>
          <option value="title">按标题</option>
          <option value="starred">按收藏</option>
        </select>
      </div>
    </div>

    <!-- 文献列表 -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
      <!-- 表头 -->
      <div class="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div class="grid grid-cols-12 gap-3 items-center text-xs font-medium text-gray-500">
          <div class="col-span-1 w-12 flex items-center justify-center">
            <input type="checkbox" v-model="headerCheckbox" @change="onHeaderCheckboxChange" class="w-4 h-4 rounded border-gray-300">
          </div>
          <div :class="currentLibraryType === 'public' ? 'col-span-4' : 'col-span-5'">文献信息</div>
          <div v-if="currentLibraryType === 'public'" class="col-span-1 text-center">上传者</div>
          <div class="col-span-1 text-center">分类</div>
          <div class="col-span-1 text-center">年份</div>
          <div class="col-span-1 text-center">状态</div>
          <div v-if="currentLibraryType === 'public'" class="col-span-1 text-center">上传时间</div>
          <div class="col-span-2 text-center">操作</div>
        </div>
      </div>

      <!-- 文献列表内容 -->
      <div>
        <div v-if="papers.length > 0">
          <div v-for="paper in papers" :key="paper.id"
               :class="selectedPapers.includes(paper.id) ? 'bg-blue-50 border-l-4 border-l-primary' : ''"
               class="px-4 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors">
            <div class="grid grid-cols-12 gap-3 items-center">
              <div class="col-span-1 w-12 flex items-center justify-center">
                <input type="checkbox" :checked="selectedPapers.includes(paper.id)"
                       @change="onPaperCheckboxChange(paper.id)"
                       class="w-4 h-4 rounded border-gray-300">
              </div>
              <div :class="currentLibraryType === 'public' ? 'col-span-4' : 'col-span-5'" class="flex items-center gap-3 cursor-pointer" @click="openDetail(paper.id)">
                <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                  <i class="fa fa-file-pdf-o text-blue-500 text-lg"></i>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="font-medium text-primary truncate">{{ paper.title }}</h3>
                    <i v-if="paper.is_starred" class="fa fa-star text-yellow-500 ml-1" title="已收藏"></i>
                  </div>
                  <p class="text-xs text-gray-500 mt-1 line-clamp-1">{{ paper.abstract || '' }}</p>
                </div>
              </div>
              <div v-if="currentLibraryType === 'public'" class="col-span-1 text-center text-sm text-gray-600">
                {{ paper.uploader_name || '-' }}
              </div>
              <div class="col-span-1 text-center">
                <div class="flex flex-wrap gap-1 justify-center">
                  <span v-for="t in (paper.tags || [])" :key="t.name"
                        :class="t.tag_type === 'system' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'"
                        class="px-2 py-1 rounded text-xs font-medium">{{ t.name }}</span>
                </div>
              </div>
              <div class="col-span-1 text-center text-sm text-gray-600">{{ paper.year || '-' }}</div>
              <div class="col-span-1 text-center">
                <span :class="statusStyle(paper.read_status)" class="px-2 py-1 rounded-full text-xs">{{ statusText(paper.read_status) }}</span>
              </div>
              <div v-if="currentLibraryType === 'public'" class="col-span-1 text-center text-xs text-gray-500">
                {{ formatDate(paper.created_at) }}
              </div>
              <div class="col-span-2 text-center">
                <div class="flex gap-1 justify-center flex-wrap">
                  <button @click="toggleStar(paper.id)" class="p-2 hover:bg-yellow-50 rounded transition-colors text-lg" title="收藏">
                    {{ paper.is_starred ? '⭐' : '☆' }}
                  </button>
                  <button v-if="currentLibraryType === 'public'" @click="addToPersonal(paper.id)" class="p-2 hover:bg-blue-50 rounded transition-colors" title="加入我的文献库">
                    <i class="fa fa-folder-o text-blue-500"></i>
                  </button>
                  <button v-if="currentLibraryType === 'private'" @click="shareToTeam(paper.id)" class="p-2 hover:bg-green-50 rounded transition-colors" title="分享到团队">
                    <i class="fa fa-share text-green-500"></i>
                  </button>
                  <button @click="openEditModal(paper.id)" class="p-2 hover:bg-gray-100 rounded transition-colors" title="编辑">
                    <i class="fa fa-edit text-gray-500"></i>
                  </button>
                  <button @click="downloadPaper(paper.id)" class="p-2 hover:bg-gray-100 rounded transition-colors" title="下载">
                    <i class="fa fa-download text-gray-500"></i>
                  </button>
                  <button @click="deletePaper(paper.id)" class="p-2 hover:bg-red-50 rounded transition-colors" title="删除">
                    <i class="fa fa-trash-o text-red-500"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="p-8 text-center text-gray-500">暂无文献数据</div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="mt-6 px-4 py-3 bg-white rounded-lg border border-gray-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">每页显示</label>
            <select v-model="pageSize" @change="onPageSizeChange" class="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="5">5条</option>
              <option value="10">10条</option>
              <option value="20">20条</option>
              <option value="50">50条</option>
            </select>
          </div>
          <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ totalCount }} 条</div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="prevPage" :disabled="currentPage <= 1"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <i class="fa fa-chevron-left mr-1"></i>上一页
          </button>
          <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
          <button @click="nextPage" :disabled="currentPage >= totalPages"
                  class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            下一页<i class="fa fa-chevron-right ml-1"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 文献详情模态框 -->
    <PaperDetailModal
      v-model="detailModalVisible"
      :paper="currentPaper"
      :library-type="currentLibraryType"
      @update="onDetailUpdate"
      @edit="openEditModal"
      @close="detailModalVisible = false"
    />

    <!-- 添加/编辑文献模态框 -->
    <PaperEditModal
      v-model="editModalVisible"
      :paper-id="editPaperId"
      :library-type="currentLibraryType"
      @saved="onPaperSaved"
      @close="editModalVisible = false"
    />

    <!-- 批量设置标签模态框 -->
    <BatchTagModal
      v-model="batchTagModalVisible"
      :selected-papers="selectedPapers"
      :library-type="currentLibraryType"
      @applied="onBatchTagApplied"
      @close="batchTagModalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { paperApi } from '../api/paper'
import PaperDetailModal from '../components/PaperDetailModal.vue'
import PaperEditModal from '../components/PaperEditModal.vue'
import BatchTagModal from '../components/BatchTagModal.vue'

// 库类型
const currentLibraryType = ref('public')

// 统计
const stats = ref({ total: 0, unread: 0, starred: 0, recent: 0 })

// 文献数据
const papers = ref([])
const tags = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(5)
const sortBy = ref('newest')

// 筛选
const keyword = ref('')
const currentTag = ref('')
const currentStatus = ref('')
const currentStarred = ref('')

// 选择模式
const selectMode = ref(false)
const selectedPapers = ref([])
const headerCheckbox = ref(false)

// 模态框
const detailModalVisible = ref(false)
const editModalVisible = ref(false)
const batchTagModalVisible = ref(false)
const currentPaper = ref(null)
const editPaperId = ref(null)

// 计算属性
const libraryTitle = computed(() => currentLibraryType.value === 'public' ? '团队文献库' : '我的文献库')
const libraryDesc = computed(() => currentLibraryType.value === 'public' ? '管理和分享团队学术文献资源' : '管理个人收藏的学术文献')

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value) || 1)
const startItem = computed(() => (currentPage.value - 1) * pageSize.value + 1)
const endItem = computed(() => Math.min(currentPage.value * pageSize.value, totalCount.value))

const libraryBtnClass = (type) => {
  if (currentLibraryType.value === type) {
    return 'bg-primary text-white'
  }
  return 'border border-gray-200 hover:bg-gray-50'
}

const statusStyle = (status) => {
  const styles = {
    unread: 'bg-gray-100 text-gray-700',
    reading: 'bg-yellow-100 text-yellow-700',
    read: 'bg-green-100 text-green-700'
  }
  return styles[status] || 'bg-gray-100 text-gray-700'
}

const statusText = (status) => {
  const texts = { unread: '未读', reading: '在读', read: '已读' }
  return texts[status] || '未读'
}

// 搜索延迟
let searchTimeout = null
const onSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadPapers()
  }, 300)
}

// 加载文献列表
const loadPapers = async () => {
  try {
    const starredValue = currentStarred.value === 'starred' ? true : currentStarred.value === 'unstarred' ? false : null

    const params = {
      library_type: currentLibraryType.value,
      keyword: keyword.value || undefined,
      tag: currentTag.value || undefined,
      status: currentStatus.value || undefined,
      starred: starredValue,
      sort: sortBy.value,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }

    const res = await paperApi.getPapers(params)
    if (res.data.success) {
      papers.value = res.data.data || []
      totalCount.value = res.data.total || 0
    }
  } catch (e) {
    console.error('加载文献失败:', e)
  }
}

// 加载统计
const loadStats = async () => {
  try {
    const res = await paperApi.getStats(currentLibraryType.value)
    if (res.data.success) {
      stats.value = res.data.data || {}
    }
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

// 加载标签
const loadTags = async () => {
  try {
    const res = await paperApi.getTags()
    if (res.data.success) {
      tags.value = res.data.data || []
    }
  } catch (e) {
    console.error('加载标签失败:', e)
  }
}

// 切换库类型
const switchLibrary = (type) => {
  currentLibraryType.value = type
  currentPage.value = 1
  loadPapers()
  loadStats()
}

// 分页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadPapers()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadPapers()
  }
}

const onPageSizeChange = () => {
  currentPage.value = 1
  loadPapers()
}

// 清除筛选
const clearFilters = () => {
  keyword.value = ''
  currentTag.value = ''
  currentStatus.value = ''
  currentStarred.value = ''
  currentPage.value = 1
  loadPapers()
}

// 选择模式
const toggleSelectMode = () => {
  selectMode.value = !selectMode.value
  if (!selectMode.value) {
    selectedPapers.value = []
    headerCheckbox.value = false
  }
}

const onHeaderCheckboxChange = () => {
  if (headerCheckbox.value) {
    selectedPapers.value = papers.value.map(p => p.id)
  } else {
    selectedPapers.value = []
  }
}

const onPaperCheckboxChange = (paperId) => {
  const index = selectedPapers.value.indexOf(paperId)
  if (index > -1) {
    selectedPapers.value.splice(index, 1)
  } else {
    selectedPapers.value.push(paperId)
  }
  headerCheckbox.value = selectedPapers.value.length === papers.value.length && papers.value.length > 0
}

const selectAll = () => {
  selectedPapers.value = papers.value.map(p => p.id)
  headerCheckbox.value = true
}

const cancelSelection = () => {
  selectedPapers.value = []
  headerCheckbox.value = false
}

// 文献操作
const openDetail = async (paperId) => {
  try {
    const res = await paperApi.getPaperDetail(paperId, currentLibraryType.value)
    if (res.data.success) {
      currentPaper.value = res.data.data
      detailModalVisible.value = true
    }
  } catch (e) {
    console.error('获取详情失败:', e)
  }
}

const toggleStar = async (paperId) => {
  try {
    const res = await paperApi.toggleStar(paperId, currentLibraryType.value)
    if (res.data.success) {
      loadPapers()
      loadStats()
    }
  } catch (e) {
    console.error('收藏失败:', e)
  }
}

const downloadPaper = (paperId) => {
  paperApi.downloadPaper(paperId, currentLibraryType.value)
}

const deletePaper = async (paperId) => {
  if (!confirm('确定删除此文献吗？')) return
  try {
    const res = await paperApi.deletePaper(paperId, currentLibraryType.value)
    if (res.data.success) {
      showToast('删除成功', 'success')
      loadPapers()
      loadStats()
    } else {
      showToast(res.data.message || '删除失败', 'error')
    }
  } catch (e) {
    console.error('删除失败:', e)
    showToast('删除失败', 'error')
  }
}

const addToPersonal = async (paperId) => {
  try {
    const res = await paperApi.addToPersonal(paperId)
    if (res.data.success) {
      showToast('已添加到个人文献库', 'success')
    } else {
      showToast(res.data.message || '添加失败', 'error')
    }
  } catch (e) {
    console.error('添加失败:', e)
    showToast('添加失败', 'error')
  }
}

const shareToTeam = async (paperId) => {
  if (!confirm('确定分享到团队文献库？')) return
  try {
    const res = await paperApi.shareToTeam(paperId)
    if (res.data.success) {
      showToast('已分享到团队文献库', 'success')
    } else {
      showToast(res.data.message || '分享失败', 'error')
    }
  } catch (e) {
    console.error('分享失败:', e)
    showToast('分享失败', 'error')
  }
}

// 编辑模态框
const openAddModal = () => {
  editPaperId.value = null
  editModalVisible.value = true
}

const openEditModal = async (paperId) => {
  editPaperId.value = paperId
  editModalVisible.value = true
}

const onPaperSaved = () => {
  editModalVisible.value = false
  loadPapers()
  loadStats()
  showToast('文献保存成功', 'success')
}

const onDetailUpdate = () => {
  loadPapers()
  loadStats()
}

// 批量操作
const batchStar = async (star) => {
  if (selectedPapers.value.length === 0) {
    showToast('请先选择文献', 'error')
    return
  }
  try {
    const res = await paperApi.batchStar(selectedPapers.value, star, currentLibraryType.value)
    if (res.data.success) {
      showToast(`已批量${star ? '收藏' : '取消收藏'}`, 'success')
      cancelSelection()
      loadPapers()
      loadStats()
    }
  } catch (e) {
    console.error('批量收藏失败:', e)
    showToast('批量收藏失败', 'error')
  }
}

const openBatchTagModal = () => {
  if (selectedPapers.value.length === 0) {
    showToast('请先选择文献', 'error')
    return
  }
  batchTagModalVisible.value = true
}

const onBatchTagApplied = () => {
  batchTagModalVisible.value = false
  cancelSelection()
  loadPapers()
  showToast('批量设置标签成功', 'success')
}

const batchDelete = async () => {
  if (selectedPapers.value.length === 0) {
    showToast('请先选择文献', 'error')
    return
  }
  if (!confirm(`确定删除 ${selectedPapers.value.length} 篇文献吗？`)) return
  try {
    const res = await paperApi.batchDelete(selectedPapers.value, currentLibraryType.value)
    if (res.data.success) {
      showToast('批量删除成功', 'success')
      cancelSelection()
      loadPapers()
      loadStats()
    } else {
      showToast(res.data.message || '批量删除失败', 'error')
    }
  } catch (e) {
    console.error('批量删除失败:', e)
    showToast('批量删除失败', 'error')
  }
}

// 辅助函数
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.split('.')[0].replace('T', ' ')
}

const showToast = (message, type = 'success') => {
  const toastDiv = document.createElement('div')
  const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500'
  const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-times-circle' : 'fa-info-circle'
  toastDiv.className = `fixed top-4 left-1/2 -translate-x-1/2 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-2 z-50`
  toastDiv.innerHTML = `<i class="fa ${icon}"></i><span>${message}</span>`
  document.body.appendChild(toastDiv)
  setTimeout(() => toastDiv.remove(), 3000)
}

// 初始化
onMounted(() => {
  loadPapers()
  loadStats()
  loadTags()
})
</script>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>