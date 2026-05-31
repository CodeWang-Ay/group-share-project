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
        <button v-if="canManage" @click="handleCreateClick" class="bg-gradient-to-r from-primary to-primary/80 text-white px-4 py-2 rounded-lg hover:from-primary/90 hover:to-primary/70 shadow-sm">
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
    <MeetingCalendar v-else-if="viewMode === 'calendar'" :meetings="allMeetings" :current-month="currentMonth" @prev="prevMonth" @next="nextMonth" @today="goToday" @view="viewMeeting" @edit="editMeeting" @create="createMeetingOnDate" @switchView="viewMode = $event" />

    <!-- 分页组件 -->
    <div v-if="viewMode !== 'calendar' && pagination.total > 0" class="mt-6 px-4 py-4 bg-white rounded-lg border flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-600">每页显示</label>
          <select v-model="pageSize" @change="loadMeetings(1)" class="px-3 py-1 border rounded-lg text-sm">
            <option :value="5">5条</option>
            <option :value="10">10条</option>
            <option :value="20">20条</option>
          </select>
        </div>
        <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ pagination.total }} 条</div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="loadMeetings(pagination.page - 1)" :disabled="pagination.page <= 1"
                class="px-3 py-1 text-sm border rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          <i class="fa fa-chevron-left mr-1"></i>上一页
        </button>
        <span class="px-3 py-1 text-sm text-gray-600">第 {{ pagination.page }} 页</span>
        <button @click="loadMeetings(pagination.page + 1)" :disabled="pagination.page >= pagination.pages"
                class="px-3 py-1 text-sm border rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          下一页<i class="fa fa-chevron-right ml-1"></i>
        </button>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <MeetingModal v-if="showCreateModal || showEditModal" :meeting="editingMeeting" :mode="modalMode" :preset-date-time="presetDateTime" @close="closeModal" @save="saveMeeting" />

    <!-- 详情弹窗 -->
    <MeetingDetail v-model="showDetailModal" :meeting="viewingMeeting" @edit="editFromDetail" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { meetingApi } from '../api/meeting'
import MeetingList from '../components/MeetingList.vue'
import MeetingGrid from '../components/MeetingGrid.vue'
import MeetingCalendar from '../components/MeetingCalendar.vue'
import MeetingModal from '../components/MeetingModal.vue'
import MeetingDetail from '../components/MeetingDetail.vue'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()
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
const pageSize = ref(5)
const currentMonth = ref(new Date())

const modalMode = computed(() => showEditModal.value ? 'edit' : 'create')

// 权限判断：只有导师和管理员可以管理组会
const canManage = computed(() => {
  return userStore.role === 'admin' || userStore.role === 'teacher'
})

// 分页显示的计算属性
const startItem = computed(() => (pagination.value.page - 1) * pageSize.value + 1)
const endItem = computed(() => Math.min(pagination.value.page * pageSize.value, pagination.value.total))

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
    let meetingId
    if (modalMode.value === 'edit') {
      // 更新组会基本信息（不包含汇报人）
      await meetingApi.update(editingMeeting.value.id, {
        title: data.title,
        meeting_type: data.meeting_type,
        duration_total: data.duration_total,
        scheduled_at: data.scheduled_at,
        location: data.location,
        is_online: data.is_online,
        online_link: data.online_link,
        description: data.description,
        material_required: data.material_required,
        status: data.status,
        notes: data.notes
      })
      meetingId = editingMeeting.value.id

      // 处理汇报人：先获取现有汇报人，再对比添加/删除
      const existingPresenters = await meetingApi.getPresenters(meetingId)
      const existingIds = (existingPresenters.data.data?.presenters || []).map(p => p.user_id)
      const newIds = data.presenter_ids || []

      // 删除不再需要的汇报人
      for (const p of (existingPresenters.data.data?.presenters || [])) {
        if (!newIds.includes(p.user_id)) {
          await meetingApi.removePresenter(meetingId, p.id)
        }
      }

      // 添加新的汇报人
      for (const presenterId of newIds) {
        if (!existingIds.includes(presenterId)) {
          // 查找对应的时长
          const duration = (data.presenter_durations || []).find(pd => pd.id === presenterId)?.duration || 15
          await meetingApi.addPresenter(meetingId, {
            user_id: presenterId,
            duration_minutes: duration,
            presenter_type: 'assigned'
          })
        }
      }
    } else {
      // 创建组会
      const res = await meetingApi.create({
        title: data.title,
        meeting_type: data.meeting_type,
        duration_total: data.duration_total,
        scheduled_at: data.scheduled_at,
        location: data.location,
        is_online: data.is_online,
        online_link: data.online_link,
        description: data.description,
        material_required: data.material_required,
        notes: data.notes
      })
      meetingId = res.data.data?.id

      // 添加汇报人
      if (meetingId && data.presenter_ids?.length) {
        for (const presenterId of data.presenter_ids) {
          const duration = (data.presenter_durations || []).find(pd => pd.id === presenterId)?.duration || 15
          await meetingApi.addPresenter(meetingId, {
            user_id: presenterId,
            duration_minutes: duration,
            presenter_type: 'assigned'
          })
        }
      }
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

// 监听路由参数变化，自动打开详情弹窗
watch(() => route.query.id, (newId) => {
  if (newId) {
    openDetailFromId(parseInt(newId))
  }
}, { immediate: true })

// 根据 ID 打开详情弹窗
async function openDetailFromId(meetingId) {
  if (!meetingId) return
  try {
    const res = await meetingApi.getDetail(meetingId)
    if (res.data.success) {
      viewingMeeting.value = res.data.data
      showDetailModal.value = true
    }
  } catch (e) {
    console.error('加载组会详情失败:', e)
  }
  // 清理 URL 参数，避免刷新时重复打开
  router.replace({ query: {} })
}

onMounted(() => {
  loadStats()
  loadMeetings()
  loadAllMeetings()  // 默认日历视图需要加载全部数据
})
</script>