<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold">{{ title }}</h1>
      <p class="text-gray-500">欢迎回来，{{ userStore.username }}！这里是您的组会和研究管理中心</p>
    </div>

    <!-- 即将到来的组会 -->
    <div class="mb-8">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">即将到来的组会</h2>
        <a href="/gm_meeting_schedule" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 flex items-center gap-2">
          <i class="fa fa-plus"></i>
          <span>安排新组会</span>
        </a>
      </div>
      <MeetingCard :meeting="upcomingMeeting" :loading="loading.upcoming" />
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <StatCard title="本月组会次数" :value="stats.month_meetings" icon="fa-calendar-check-o" color="primary">
        <template #trend>
          <span :class="meetingsTrendClass">
            <i :class="meetingsTrendIcon"></i>
            {{ meetingsTrendText }}
          </span>
        </template>
      </StatCard>
      <StatCard title="待审阅材料" :value="stats.pending_materials" icon="fa-file-text-o" color="secondary">
        <template #footer>
          <a href="/gm_report_materials" class="text-primary hover:underline text-sm">
            立即审阅 <i class="fa fa-arrow-right ml-1 text-xs"></i>
          </a>
        </template>
      </StatCard>
      <StatCard title="团队成员" :value="stats.team_members" icon="fa-users" color="accent">
        <template #footer>
          <span class="text-gray-500 text-sm">博士{{ stats.phd_count }}人，硕士{{ stats.master_count }}人</span>
        </template>
      </StatCard>
      <StatCard title="共享文献" :value="stats.total_papers" icon="fa-book" color="orange">
        <template #trend>
          <span class="text-gray-500 text-sm">
            <i class="fa fa-arrow-up mr-1"></i> 本月新增{{ stats.month_new_papers }}篇
          </span>
        </template>
      </StatCard>
    </div>

    <!-- 最近提交的材料和文献库 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <FileList title="最近提交的材料" :files="recentFiles" :loading="loading.files" />
      <PaperList title="团队文献库" :papers="recentPapers" :loading="loading.papers" />
    </div>

    <!-- 研究进展跟踪 -->
    <ProgressTable :progress="recentProgress" :loading="loading.progress" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { dashboardApi } from '../api/dashboard'
import StatCard from '../components/StatCard.vue'
import MeetingCard from '../components/MeetingCard.vue'
import FileList from '../components/FileList.vue'
import PaperList from '../components/PaperList.vue'
import ProgressTable from '../components/ProgressTable.vue'

const userStore = useUserStore()

const title = computed(() => {
  if (userStore.role === 'admin') return '管理员工作台'
  if (userStore.role === 'teacher') return '导师工作台'
  return '学生工作台'
})

const loading = ref({
  stats: true,
  upcoming: true,
  files: true,
  papers: true,
  progress: true
})

const stats = ref({
  month_meetings: 0,
  last_month_meetings: 0,
  pending_materials: 0,
  team_members: 0,
  phd_count: 0,
  master_count: 0,
  total_papers: 0,
  month_new_papers: 0
})

const upcomingMeeting = ref(null)
const recentFiles = ref([])
const recentPapers = ref([])
const recentProgress = ref([])

const meetingsChange = computed(() => stats.value.month_meetings - stats.value.last_month_meetings)

const meetingsTrendClass = computed(() => {
  if (meetingsChange.value > 0) return 'text-green-500 flex items-center'
  if (meetingsChange.value < 0) return 'text-red-500 flex items-center'
  return 'text-gray-500'
})

const meetingsTrendIcon = computed(() => {
  if (meetingsChange.value > 0) return 'fa fa-arrow-up mr-1'
  if (meetingsChange.value < 0) return 'fa fa-arrow-down mr-1'
  return ''
})

const meetingsTrendText = computed(() => {
  if (meetingsChange.value > 0) return `较上月增加${meetingsChange.value}次`
  if (meetingsChange.value < 0) return `较上月减少${Math.abs(meetingsChange.value)}次`
  return '与上月持平'
})

async function loadData() {
  // 独立加载每个数据块，避免一个失败导致全部失败
  loadStats()
  loadUpcoming()
  loadFiles()
  loadPapers()
  loadProgress()
}

async function loadStats() {
  try {
    const res = await dashboardApi.getStats()
    if (res.data.success) {
      stats.value = res.data.data
      loading.value.stats = false
    }
  } catch (e) {
    console.error('加载统计数据失败:', e)
    loading.value.stats = false
  }
}

async function loadUpcoming() {
  try {
    const res = await dashboardApi.getUpcoming()
    if (res.data.success) {
      upcomingMeeting.value = res.data.data.meetings?.[0]
      loading.value.upcoming = false
    }
  } catch (e) {
    console.error('加载组会数据失败:', e)
    loading.value.upcoming = false
  }
}

async function loadFiles() {
  try {
    const res = await dashboardApi.getRecentFiles()
    if (res.data.success) {
      recentFiles.value = res.data.data.files || []
      loading.value.files = false
    }
  } catch (e) {
    console.error('加载材料数据失败:', e)
    loading.value.files = false
  }
}

async function loadPapers() {
  try {
    const res = await dashboardApi.getRecentPapers()
    if (res.data.success) {
      recentPapers.value = res.data.data.papers || []
      loading.value.papers = false
    }
  } catch (e) {
    console.error('加载文献数据失败:', e)
    loading.value.papers = false
  }
}

async function loadProgress() {
  try {
    const res = await dashboardApi.getRecentProgress()
    if (res.data.success) {
      recentProgress.value = res.data.data.progress || []
      loading.value.progress = false
    }
  } catch (e) {
    console.error('加载进展数据失败:', e)
    loading.value.progress = false
  }
}

onMounted(loadData)
</script>