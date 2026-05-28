<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <div class="mb-6">
      <h1 class="text-xl font-bold text-gray-800 mb-2">组会记录</h1>
      <p class="text-gray-500 mb-6">查看历史组会纪要、讨论内容与导师意见</p>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">总记录数</p><h3 class="text-2xl font-bold mt-1">{{ stats.total || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-primary"><i class="fa fa-file-text-o"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">已填写纪要</p><h3 class="text-2xl font-bold mt-1 text-green-600">{{ stats.filled || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600"><i class="fa fa-check-circle"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">待填写纪要</p><h3 class="text-2xl font-bold mt-1 text-orange-500">{{ stats.empty || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-500"><i class="fa fa-exclamation-circle"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-lg p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-gray-500 text-sm">汇报人总数</p><h3 class="text-2xl font-bold mt-1">{{ stats.presenters || 0 }}</h3></div>
            <div class="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600"><i class="fa fa-users"></i></div>
          </div>
        </div>
      </div>

      <!-- 工具栏 -->
      <div class="bg-white rounded-xl shadow-sm border p-4 mb-6">
        <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div class="flex flex-wrap gap-2">
            <button @click="filterByMinutes('all')" :class="filterBtnClass('all')">全部记录</button>
            <button @click="filterByMinutes('filled')" :class="filterBtnClass('filled')"><i class="fa fa-check-circle text-green-600 mr-1"></i>已填写纪要</button>
            <button @click="filterByMinutes('empty')" :class="filterBtnClass('empty')"><i class="fa fa-exclamation-circle text-orange-500 mr-1"></i>待填写纪要</button>
          </div>
          <div class="flex items-center gap-3 w-full lg:w-auto">
            <div class="relative flex-1 lg:w-64">
              <input v-model="searchKeyword" type="text" placeholder="搜索组会标题、纪要内容..."
                     class="w-full py-2 pl-10 pr-4 rounded-lg bg-gray-100 border-0 focus:ring-2 focus:ring-primary/30 focus:bg-white">
              <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
            </div>
            <!-- 布局切换按钮 -->
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
      <RecordList v-else-if="viewMode === 'list'" :records="pageRecords" :search-keyword="searchKeyword" :minutes-filter="minutesFilter"
                 @view="openDetailModal" @edit="openEditModal" @materials="openMaterialsModal" />

      <!-- 卡片视图 -->
      <RecordGrid v-else :records="pageRecords" :search-keyword="searchKeyword" :minutes-filter="minutesFilter"
                 @view="openDetailModal" @edit="openEditModal" @loadMaterials="loadMaterials" />

      <!-- 分页 -->
      <div v-if="filteredRecords.length > 0" class="mt-6 px-4 py-4 bg-white rounded-lg border flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">每页显示</label>
            <select v-model="perPage" @change="changePerPage" class="px-3 py-1 border rounded-lg text-sm">
              <option :value="5">5条</option>
              <option :value="10">10条</option>
              <option :value="20">20条</option>
            </select>
          </div>
          <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ filteredRecords.length }} 条</div>
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

    <!-- 详情模态框 -->
    <RecordDetailModal v-if="showDetailModal" :meeting="currentMeeting" @close="closeDetailModal" @edit="openEditModalFromDetail" />

    <!-- 编辑纪要模态框 -->
    <EditMinutesModal v-if="showEditModal" :meeting-id="editMeetingId" :meeting-title="editMeetingTitle" :initial-content="editMinutesContent"
                      @close="closeEditModal" @save="handleSaveMinutes" />

    <!-- 材料模态框 -->
    <MaterialsModal v-if="showMaterialsModal" :meeting-id="materialsMeetingId" :meeting-title="materialsMeetingTitle"
                    @close="closeMaterialsModal" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { recordApi } from '../api/record'
import RecordList from '../components/RecordList.vue'
import RecordGrid from '../components/RecordGrid.vue'
import RecordDetailModal from '../components/RecordDetailModal.vue'
import EditMinutesModal from '../components/EditMinutesModal.vue'
import MaterialsModal from '../components/MaterialsModal.vue'

const loading = ref(true)
const viewMode = ref('list')
const minutesFilter = ref('all')
const searchKeyword = ref('')
const perPage = ref(5)
const currentPage = ref(1)

const allRecords = ref([])
const stats = ref({ total: 0, filled: 0, empty: 0, presenters: 0 })

// 模态框状态
const showDetailModal = ref(false)
const showEditModal = ref(false)
const showMaterialsModal = ref(false)
const currentMeeting = ref(null)
const editMeetingId = ref(null)
const editMeetingTitle = ref('')
const editMinutesContent = ref('')
const materialsMeetingId = ref(null)
const materialsMeetingTitle = ref('')

let searchTimeout = null

// 计算属性
const filteredRecords = computed(() => {
  let records = allRecords.value

  // 按纪要状态筛选
  if (minutesFilter.value === 'filled') {
    records = records.filter(m => m.minutes && m.minutes.trim())
  } else if (minutesFilter.value === 'empty') {
    records = records.filter(m => !m.minutes || !m.minutes.trim())
  }

  // 搜索筛选
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    records = records.filter(m => {
      const titleMatch = m.title && m.title.toLowerCase().includes(keyword)
      const minutesMatch = m.minutes && m.minutes.toLowerCase().includes(keyword)
      const descMatch = m.description && m.description.toLowerCase().includes(keyword)
      return titleMatch || minutesMatch || descMatch
    })
  }

  return records
})

const totalPages = computed(() => Math.ceil(filteredRecords.value.length / perPage.value) || 1)
const startItem = computed(() => (currentPage.value - 1) * perPage.value + 1)
const endItem = computed(() => Math.min(currentPage.value * perPage.value, filteredRecords.value.length))

const pageRecords = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  const end = start + perPage.value
  return filteredRecords.value.slice(start, end)
})

function filterBtnClass(status) {
  return minutesFilter.value === status
    ? 'px-3 py-1 bg-primary text-white text-sm rounded-lg transition-colors'
    : 'px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-lg hover:bg-gray-200 transition-colors'
}

function viewBtnClass(mode) {
  return viewMode.value === mode
    ? 'px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 bg-white text-gray-900 shadow-sm'
    : 'px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 text-gray-500 hover:text-gray-700'
}

function filterByMinutes(status) {
  minutesFilter.value = status
  currentPage.value = 1
}

function changePerPage() {
  currentPage.value = 1
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value--
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++
}

async function loadRecords() {
  loading.value = true
  try {
    const res = await recordApi.getMeetings({ status: 'completed', limit: 100 })
    if (res.data.success) {
      allRecords.value = res.data.data.meetings || []
      updateStats()
    }
  } catch (e) {
    console.error('加载组会记录失败:', e)
  }
  loading.value = false
}

function updateStats() {
  const records = allRecords.value
  stats.value.total = records.length
  stats.value.filled = records.filter(m => m.minutes && m.minutes.trim()).length
  stats.value.empty = records.length - stats.value.filled

  let presenterCount = 0
  records.forEach(m => {
    if (m.presenters) presenterCount += m.presenters.length
  })
  stats.value.presenters = presenterCount
}

async function openDetailModal(meeting) {
  try {
    const res = await recordApi.getMeetingDetail(meeting.id)
    if (res.data.success) {
      currentMeeting.value = res.data.data
      showDetailModal.value = true
    } else {
      window.$toast?.(res.data.message || '获取详情失败', 'error')
    }
  } catch (e) {
    console.error('获取详情失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

function closeDetailModal() {
  showDetailModal.value = false
  currentMeeting.value = null
}

function openEditModal(meetingId, title, minutes) {
  editMeetingId.value = meetingId
  editMeetingTitle.value = title
  editMinutesContent.value = minutes || ''
  showEditModal.value = true
  closeDetailModal()
}

function openEditModalFromDetail(meeting) {
  openEditModal(meeting.id, meeting.title, meeting.minutes)
}

function closeEditModal() {
  showEditModal.value = false
  editMeetingId.value = null
  editMeetingTitle.value = ''
  editMinutesContent.value = ''
}

async function handleSaveMinutes(content) {
  try {
    const res = await recordApi.updateMinutes(editMeetingId.value, content)
    if (res.data.success) {
      window.$toast?.('会议纪要保存成功', 'success')
      closeEditModal()
      loadRecords()
    } else {
      window.$toast?.(res.data.message || '保存失败', 'error')
    }
  } catch (e) {
    console.error('保存纪要失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

function openMaterialsModal(meetingId, title) {
  materialsMeetingId.value = meetingId
  materialsMeetingTitle.value = title
  showMaterialsModal.value = true
}

function closeMaterialsModal() {
  showMaterialsModal.value = false
  materialsMeetingId.value = null
  materialsMeetingTitle.value = ''
}

function loadMaterials(_meetingId) {
  // 由RecordGrid组件内部处理
}

onMounted(() => {
  loadRecords()
})

watch(minutesFilter, () => { currentPage.value = 1 })
watch(searchKeyword, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => { currentPage.value = 1 }, 300)
})
</script>