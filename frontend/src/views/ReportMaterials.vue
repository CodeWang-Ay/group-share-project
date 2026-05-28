<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-800 mb-2">汇报材料</h1>
      <p class="text-gray-500 mb-6">按组会查看和管理汇报材料，点击组会卡片选择汇报人上传材料</p>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">组会总数</p><h3 class="text-2xl font-bold mt-1">{{ stats.total_meetings || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-primary"><i class="fa fa-calendar"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">待提交材料</p><h3 class="text-2xl font-bold mt-1 text-orange-500">{{ stats.pending || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-500"><i class="fa fa-exclamation-circle"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">已提交待审核</p><h3 class="text-2xl font-bold mt-1 text-yellow-600">{{ stats.submitted || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-600"><i class="fa fa-clock-o"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">材料已通过</p><h3 class="text-2xl font-bold mt-1 text-green-600">{{ stats.approved || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600"><i class="fa fa-check-circle"></i></div>
          </div>
        </div>
      </div>

      <!-- 筛选栏 -->
      <div class="bg-white rounded-xl shadow-sm border p-4 mb-6">
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div class="flex flex-wrap gap-2">
            <button @click="filterByStatus('all')" :class="filterBtnClass('all')">全部组会</button>
            <button @click="filterByStatus('pending')" :class="filterBtnClass('pending')"><i class="fa fa-exclamation-circle mr-1 text-orange-500"></i>有待提交</button>
            <button @click="filterByStatus('submitted')" :class="filterBtnClass('submitted')"><i class="fa fa-clock-o mr-1 text-yellow-600"></i>待审核</button>
            <button @click="filterByStatus('approved')" :class="filterBtnClass('approved')"><i class="fa fa-check-circle mr-1 text-green-600"></i>已完成</button>
          </div>
          <div class="flex items-center gap-3 w-full lg:w-auto">
            <div class="relative flex-1 lg:w-64">
              <input v-model="searchKeyword" @keyup.enter="handleSearch" type="text" placeholder="搜索组会标题..."
                     class="w-full py-2 pl-10 pr-4 rounded-lg bg-gray-100 border-0 focus:ring-2 focus:ring-primary/30 focus:bg-white">
              <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
            </div>
            <!-- 视图切换按钮 -->
            <div class="bg-gray-100 rounded-lg p-1 flex">
              <button @click="viewMode = 'list'" :class="viewBtnClass('list')" title="列表视图">
                <i class="fa fa-list"></i>
              </button>
              <button @click="viewMode = 'grid'" :class="viewBtnClass('grid')" title="卡片视图">
                <i class="fa fa-th-large"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        <i class="fa fa-spinner fa-spin mr-2"></i>加载中...
      </div>

      <!-- 列表视图 -->
      <MaterialList v-else-if="viewMode === 'list'" :meetings="meetings" :search-keyword="searchKeyword"
                    @detail="openDetailModal" @upload="openPresenterModal" />

      <!-- 卡片视图 -->
      <MaterialGrid v-else :meetings="meetings" :search-keyword="searchKeyword"
                    @detail="openDetailModal" @upload="openPresenterModal" />

      <!-- 分页 -->
      <div v-if="pagination.total > 0" class="mt-6 px-4 py-3 bg-white rounded-lg border flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">每页显示</label>
            <select v-model="perPage" @change="changePerPage" class="px-3 py-1 border rounded-lg text-sm focus:ring-2 focus:ring-primary/30">
              <option :value="5">5条</option>
              <option :value="10">10条</option>
              <option :value="20">20条</option>
            </select>
          </div>
          <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ pagination.total }} 条</div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="prevPage" :disabled="currentPage <= 1"
                  class="px-3 py-1 text-sm border rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <i class="fa fa-chevron-left mr-1"></i>上一页
          </button>
          <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
          <button @click="nextPage" :disabled="currentPage >= totalPages"
                  class="px-3 py-1 text-sm border rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            下一页<i class="fa fa-chevron-right ml-1"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 汇报人选择模态框 -->
    <PresenterModal v-if="showPresenterModal" :meeting-id="currentMeetingId" :meeting-title="currentMeetingTitle"
                    :user-id="userStore.userInfo?.id" @close="closePresenterModal" @upload="openUploadModal" />

    <!-- 上传材料模态框 -->
    <UploadModal v-if="showUploadModal" :presenter-id="uploadPresenterId" :meeting-id="uploadMeetingId"
                 :presenter-name="uploadPresenterName" :meeting-title="uploadMeetingTitle"
                 @close="closeUploadModal" @success="handleUploadSuccess" />

    <!-- 组会详情模态框 -->
    <DetailModal v-if="showDetailModal" :meeting="detailMeeting" :user-id="userStore.userInfo?.id"
                 @close="closeDetailModal" @confirm="handleConfirmAttendance" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '../stores/user'
import { materialApi } from '../api/material'
import MaterialGrid from '../components/MaterialGrid.vue'
import MaterialList from '../components/MaterialList.vue'
import PresenterModal from '../components/PresenterModal.vue'
import UploadModal from '../components/UploadModal.vue'
import DetailModal from '../components/DetailModal.vue'

const userStore = useUserStore()
const loading = ref(true)
const viewMode = ref('list')
const statusFilter = ref('all')
const searchKeyword = ref('')
const perPage = ref(10)
const currentPage = ref(1)
let searchTimeout = null

const stats = ref({})
const meetings = ref([])
const pagination = ref({ total: 0, total_pages: 1 })

// 模态框状态
const showPresenterModal = ref(false)
const showUploadModal = ref(false)
const showDetailModal = ref(false)
const currentMeetingId = ref(null)
const currentMeetingTitle = ref('')
const uploadPresenterId = ref(null)
const uploadMeetingId = ref(null)
const uploadPresenterName = ref('')
const uploadMeetingTitle = ref('')
const detailMeeting = ref(null)

// 计算属性
const totalPages = computed(() => pagination.value.total_pages || 1)
const startItem = computed(() => (currentPage.value - 1) * perPage.value + 1)
const endItem = computed(() => Math.min(currentPage.value * perPage.value, pagination.value.total))

function filterBtnClass(status) {
  return statusFilter.value === status
    ? 'px-3 py-1 bg-primary text-white text-sm rounded-lg transition-colors'
    : 'px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-lg hover:bg-gray-200 transition-colors'
}

function viewBtnClass(mode) {
  return viewMode.value === mode
    ? 'px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 bg-white text-gray-900 shadow-sm'
    : 'px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 text-gray-500 hover:text-gray-700'
}

function filterByStatus(status) {
  statusFilter.value = status
  currentPage.value = 1
  loadMeetings()
}

function handleSearch() {
  currentPage.value = 1
  loadMeetings()
}

function changePerPage() {
  currentPage.value = 1
  loadMeetings()
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    loadMeetings()
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadMeetings()
  }
}

async function loadMeetings() {
  loading.value = true
  try {
    const params = { page: currentPage.value, limit: perPage.value }
    if (statusFilter.value !== 'all') params.material_status = statusFilter.value
    if (searchKeyword.value) params.search = searchKeyword.value

    const res = await materialApi.getMeetings(params)
    if (res.data.success) {
      meetings.value = res.data.data.meetings || []
      stats.value = res.data.data.stats || {}
      pagination.value = {
        total: res.data.data.pagination?.total || 0,
        total_pages: res.data.data.pagination?.total_pages || 1
      }
    }
  } catch (e) {
    console.error('加载组会材料失败:', e)
  }
  loading.value = false
}

function openPresenterModal(meetingId, meetingTitle) {
  currentMeetingId.value = meetingId
  currentMeetingTitle.value = meetingTitle
  showPresenterModal.value = true
}

function closePresenterModal() {
  showPresenterModal.value = false
  currentMeetingId.value = null
  currentMeetingTitle.value = ''
}

function openUploadModal(presenterId, meetingId, presenterName, meetingTitle) {
  uploadPresenterId.value = presenterId
  uploadMeetingId.value = meetingId
  uploadPresenterName.value = presenterName
  uploadMeetingTitle.value = meetingTitle
  showUploadModal.value = true
}

function closeUploadModal() {
  showUploadModal.value = false
  uploadPresenterId.value = null
  uploadMeetingId.value = null
  uploadPresenterName.value = ''
  uploadMeetingTitle.value = ''
}

function handleUploadSuccess() {
  closeUploadModal()
  closePresenterModal()
  loadMeetings()
}

function openDetailModal(meeting) {
  detailMeeting.value = meeting
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  detailMeeting.value = null
}

async function handleConfirmAttendance(presenterId) {
  try {
    const res = await materialApi.confirmAttendance(presenterId)
    if (res.data.success) {
      window.$toast?.('已确认参会', 'success')
      loadMeetings()
      closeDetailModal()
    } else {
      window.$toast?.(res.data.message || '确认失败', 'error')
    }
  } catch (e) {
    console.error('确认参会失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

onMounted(() => {
  loadMeetings()
})

watch(statusFilter, () => {
  currentPage.value = 1
  loadMeetings()
})

// 搜索关键词变化时触发搜索（300ms延迟）
watch(searchKeyword, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadMeetings()
  }, 300)
})
</script>