<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold">组会安排</h1>
      <p class="text-gray-500">管理实验室组会日程和安排</p>
    </div>

    <!-- 统计卡片（日历视图时隐藏，因为侧边栏已有统计） -->
    <div v-if="viewMode !== 'calendar'" class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-sm p-4 border">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">本月组会</p>
            <h3 class="text-xl font-bold">{{ stats.this_month_meetings || 0 }}</h3>
          </div>
          <i class="fa fa-calendar text-primary text-xl"></i>
        </div>
      </div>
      <div class="bg-white rounded-lg shadow-sm p-4 border">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">待召开</p>
            <h3 class="text-xl font-bold">{{ stats.scheduled_count || 0 }}</h3>
          </div>
          <i class="fa fa-clock-o text-orange-500 text-xl"></i>
        </div>
      </div>
      <div class="bg-white rounded-lg shadow-sm p-4 border">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">已召开</p>
            <h3 class="text-xl font-bold">{{ stats.completed_count || 0 }}</h3>
          </div>
          <i class="fa fa-check text-green-500 text-xl"></i>
        </div>
      </div>
      <div class="bg-white rounded-lg shadow-sm p-4 border">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm">总组会数</p>
            <h3 class="text-xl font-bold">{{ stats.total_meetings || 0 }}</h3>
          </div>
          <i class="fa fa-list text-accent text-xl"></i>
        </div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-6 flex flex-wrap gap-4 items-center justify-between">
      <div class="flex flex-wrap gap-2 items-center">
        <!-- 状态筛选按钮 -->
        <button @click="statusFilter = ''" :class="statusFilter === '' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'" class="px-3 py-1.5 text-sm rounded-lg transition-colors">
          全部状态
        </button>
        <button @click="statusFilter = 'scheduled'" :class="statusFilter === 'scheduled' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'" class="px-3 py-1.5 text-sm rounded-lg transition-colors">
          <i class="fa fa-clock-o mr-1"></i>待召开
        </button>
        <button @click="statusFilter = 'ongoing'" :class="statusFilter === 'ongoing' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'" class="px-3 py-1.5 text-sm rounded-lg transition-colors">
          <i class="fa fa-play-circle mr-1 text-green-600"></i>进行中
        </button>
        <button @click="statusFilter = 'completed'" :class="statusFilter === 'completed' ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'" class="px-3 py-1.5 text-sm rounded-lg transition-colors">
          <i class="fa fa-check-circle mr-1"></i>已召开
        </button>
        <!-- 视图切换 -->
        <div class="border-l border-gray-200 pl-2 ml-2 flex gap-2">
          <button @click="viewMode = 'calendar'" :class="viewBtnClass('calendar')">
            <i class="fa fa-calendar mr-1"></i>日历
          </button>
          <button @click="viewMode = 'list'" :class="viewBtnClass('list')">
            <i class="fa fa-list mr-1"></i>列表
          </button>
          <button @click="viewMode = 'grid'" :class="viewBtnClass('grid')">
            <i class="fa fa-th-large mr-1"></i>卡片
          </button>
        </div>
      </div>
      <div class="flex gap-2 items-center">
        <!-- 搜索框 -->
        <div class="relative">
          <input v-model="searchKeyword" @keyup.enter="handleSearch" type="text"
                 class="w-64 border-2 border-gray-200 rounded-lg px-4 py-2 pl-10 focus:border-primary focus:outline-none"
                 placeholder="搜索组会标题...">
          <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
        </div>
        <select v-model="typeFilter" class="border-2 border-gray-200 rounded-lg px-3 py-2 text-sm focus:border-primary">
          <option value="">全部类型</option>
          <option value="regular">常规组会</option>
          <option value="paper_reading">论文研读</option>
          <option value="discussion">专题讨论</option>
        </select>
        <button @click="handleCreateClick" class="bg-gradient-to-r from-primary to-primary/80 text-white px-4 py-2 rounded-lg hover:from-primary/90 hover:to-primary/70 shadow-sm">
          <i class="fa fa-plus mr-1"></i>新建组会
        </button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div v-if="loading" class="text-center py-8">
      <i class="fa fa-spinner fa-spin text-2xl text-gray-400"></i>
    </div>

    <!-- 列表视图 -->
    <MeetingList v-else-if="viewMode === 'list'" :meetings="meetings" @view="viewMeeting" @edit="editMeeting" @delete="deleteMeeting" />

    <!-- 卡片视图 -->
    <MeetingGrid v-else-if="viewMode === 'grid'" :meetings="meetings" @view="viewMeeting" @edit="editMeeting" @delete="deleteMeeting" />

    <!-- 日历视图 -->
    <MeetingCalendar v-else-if="viewMode === 'calendar'" :meetings="allMeetings" :current-month="currentMonth" @prev="prevMonth" @next="nextMonth" @today="goToday" @edit="editMeeting" @create="createMeetingOnDate" @switchView="viewMode = $event" />

    <!-- 分页组件 -->
    <div v-if="viewMode !== 'calendar' && pagination.total > 0" class="mt-6 flex justify-center items-center gap-2">
      <button @click="loadMeetings(1)" :disabled="pagination.page === 1"
              class="px-3 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <i class="fa fa-angle-double-left"></i>
      </button>
      <button @click="loadMeetings(pagination.page - 1)" :disabled="pagination.page <= 1"
              class="px-3 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <i class="fa fa-angle-left"></i>
      </button>

      <!-- 页码显示 -->
      <div class="flex gap-1">
        <button v-for="p in visiblePages" :key="p"
                @click="loadMeetings(p)"
                :class="p === pagination.page ? 'bg-primary text-white' : 'border hover:bg-gray-50'"
                class="px-3 py-2 rounded-lg transition-colors">
          {{ p }}
        </button>
      </div>

      <button @click="loadMeetings(pagination.page + 1)" :disabled="pagination.page >= pagination.pages"
              class="px-3 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <i class="fa fa-angle-right"></i>
      </button>
      <button @click="loadMeetings(pagination.pages)" :disabled="pagination.page === pagination.pages"
              class="px-3 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
        <i class="fa fa-angle-double-right"></i>
      </button>

      <!-- 总数显示和每页条数 -->
      <span class="ml-4 text-sm text-gray-500">
        共 {{ pagination.total }} 条
      </span>
      <select v-model="pageSize" @change="loadMeetings(1)" class="border rounded-lg px-2 py-1 text-sm">
        <option :value="5">5条/页</option>
        <option :value="10">10条/页</option>
        <option :value="20">20条/页</option>
      </select>
    </div>

    <!-- 创建/编辑弹窗 -->
    <MeetingModal v-if="showCreateModal || showEditModal" :meeting="editingMeeting" :mode="modalMode" :preset-date-time="presetDateTime" @close="closeModal" @save="saveMeeting" />

    <!-- 详情弹窗 -->
    <MeetingDetail v-model="showDetailModal" :meeting="viewingMeeting" @edit="editFromDetail" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '../stores/user'
import { meetingApi } from '../api/meeting'
import MeetingList from '../components/MeetingList.vue'
import MeetingGrid from '../components/MeetingGrid.vue'
import MeetingCalendar from '../components/MeetingCalendar.vue'
import MeetingModal from '../components/MeetingModal.vue'
import MeetingDetail from '../components/MeetingDetail.vue'

const userStore = useUserStore()
const loading = ref(true)
const viewMode = ref('calendar')
const statusFilter = ref('')
const typeFilter = ref('')
const searchKeyword = ref('')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDetailModal = ref(false)
const editingMeeting = ref(null)
const viewingMeeting = ref(null)
const presetDateTime = ref('')

const stats = ref({})
const meetings = ref([])
const allMeetings = ref([])
const pagination = ref({ page: 1, pages: 1, total: 0 })
const pageSize = ref(10)
const currentMonth = ref(new Date())

const modalMode = computed(() => showEditModal.value ? 'edit' : 'create')

// 计算显示的页码
const visiblePages = computed(() => {
  const pages = []
  const total = pagination.value.pages
  const current = pagination.value.page

  // 显示当前页前后各2页
  let start = Math.max(1, current - 2)
  let end = Math.min(total, current + 2)

  // 如果少于5页，显示全部
  if (total <= 5) {
    start = 1
    end = total
  } else if (current <= 3) {
    end = 5
  } else if (current >= total - 2) {
    start = total - 4
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

function viewBtnClass(mode) {
  return viewMode.value === mode
    ? 'px-3 py-2 rounded-lg bg-primary text-white'
    : 'px-3 py-2 rounded-lg border hover:bg-gray-50'
}

function handleCreateClick() {
  // 检查权限：只有导师和管理员可以创建组会
  if (userStore.role !== 'admin' && userStore.role !== 'teacher') {
    window.$toast?.('只有导师和管理员可以创建组会', 'warning')
    return
  }
  showCreateModal.value = true
}

function handleSearch() {
  loadMeetings(1)
}

async function loadStats() {
  try {
    const res = await meetingApi.getStats()
    if (res.data.success) {
      stats.value = res.data.data
    }
  } catch (e) {
    console.error('加载统计失败:', e)
  }
}

async function loadMeetings(page = 1) {
  loading.value = true
  try {
    const params = { page, limit: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    if (typeFilter.value) params.meeting_type = typeFilter.value
    if (searchKeyword.value) params.search = searchKeyword.value

    const res = await meetingApi.getList(params)
    if (res.data.success) {
      meetings.value = res.data.data.meetings || []
      const p = res.data.data.pagination || {}
      pagination.value = {
        page: p.current_page || 1,
        pages: p.total_pages || 1,
        total: p.total || 0
      }
    }
  } catch (e) {
    console.error('加载组会列表失败:', e)
  }
  loading.value = false
}

async function loadAllMeetings() {
  try {
    // 加载足够多的数据用于日历统计（最多1000条）
    const res = await meetingApi.getList({ page: 1, limit: 1000 })
    if (res.data.success) {
      allMeetings.value = res.data.data.meetings || []
    }
  } catch (e) {
    console.error('加载全部组会失败:', e)
  }
}

function viewMeeting(meeting) {
  viewingMeeting.value = meeting
  showDetailModal.value = true
}

function editMeeting(meeting) {
  editingMeeting.value = meeting
  showEditModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  viewingMeeting.value = null
}

function editFromDetail(meeting) {
  showDetailModal.value = false
  editingMeeting.value = meeting
  showEditModal.value = true
}

async function deleteMeeting(id) {
  if (!confirm('确定删除该组会？')) return
  try {
    await meetingApi.delete(id)
    loadMeetings(pagination.value.page)
    loadStats()
  } catch (e) {
    console.error('删除失败:', e)
  }
}

function closeModal() {
  showCreateModal.value = false
  showEditModal.value = false
  editingMeeting.value = null
  presetDateTime.value = ''
}

async function saveMeeting(data) {
  try {
    if (modalMode.value === 'edit') {
      await meetingApi.update(editingMeeting.value.id, data)
    } else {
      await meetingApi.create(data)
    }
    closeModal()
    loadMeetings(pagination.value.page)
    loadStats()
    loadAllMeetings()
  } catch (e) {
    console.error('保存失败:', e)
  }
}

function prevMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1)
}

function nextMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1)
}

function goToday() {
  currentMonth.value = new Date()
}

function createMeetingOnDate(date, time = '09:00') {
  // 检查权限：只有导师和管理员可以创建组会
  if (userStore.role !== 'admin' && userStore.role !== 'teacher') {
    window.$toast?.('只有导师和管理员可以创建组会', 'warning')
    return
  }
  // 设置预填充的日期时间
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  presetDateTime.value = `${year}-${month}-${day}T${time}`
  showCreateModal.value = true
}

watch([statusFilter, typeFilter, searchKeyword], () => {
  loadMeetings(1)
})

watch(viewMode, (mode) => {
  if (mode === 'calendar') {
    loadAllMeetings()
  }
})

onMounted(() => {
  loadStats()
  loadMeetings()
  loadAllMeetings()  // 默认日历视图需要加载全部数据
})
</script>