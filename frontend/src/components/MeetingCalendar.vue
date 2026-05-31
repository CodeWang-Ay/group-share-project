<template>
  <div class="flex gap-6">
    <!-- 日历核心 -->
    <div class="flex-1">
      <!-- 日历工具栏 -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-2xl border border-gray-200 p-5 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <button @click="$emit('prev')" class="w-9 h-9 rounded-xl bg-white shadow-sm border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-blue-100 hover:text-blue-600 hover:border-blue-200 transition-all duration-200">
              <i class="fa fa-chevron-left text-sm"></i>
            </button>
            <span class="text-xl font-bold text-gray-800 min-w-[150px] text-center tracking-wide">{{ monthTitle }}</span>
            <button @click="$emit('next')" class="w-9 h-9 rounded-xl bg-white shadow-sm border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-blue-100 hover:text-blue-600 hover:border-blue-200 transition-all duration-200">
              <i class="fa fa-chevron-right text-sm"></i>
            </button>
          </div>
          <button @click="$emit('today')" class="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium shadow-sm hover:bg-blue-700 transition-colors flex items-center gap-2">
            <i class="fa fa-crosshairs"></i>今天
          </button>
        </div>
        <div class="flex items-center gap-3">
          <!-- 类型筛选 -->
          <div class="relative">
            <select v-model="typeFilterLocal" class="appearance-none px-4 py-2 pr-8 bg-white border border-gray-200 rounded-xl text-sm text-gray-600 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 shadow-sm cursor-pointer">
              <option value="">全部类型</option>
              <option value="regular">常规组会</option>
              <option value="paper_reading">论文研读</option>
              <option value="discussion">专题讨论</option>
            </select>
            <i class="fa fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none"></i>
          </div>
          <!-- 状态筛选 -->
          <div class="relative">
            <select v-model="statusFilterLocal" class="appearance-none px-4 py-2 pr-8 bg-white border border-gray-200 rounded-xl text-sm text-gray-600 focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 shadow-sm cursor-pointer">
              <option value="">全部状态</option>
              <option value="scheduled">待召开</option>
              <option value="ongoing">进行中</option>
              <option value="completed">已召开</option>
              <option value="cancelled">已废弃</option>
            </select>
            <i class="fa fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-xs pointer-events-none"></i>
          </div>
        </div>
      </div>

      <!-- 日历网格 -->
      <div class="bg-white rounded-b-2xl border border-t-0 border-gray-200 overflow-hidden shadow-lg">
        <!-- 星期头部 -->
        <div class="grid grid-cols-7 bg-gradient-to-b from-gray-100 to-gray-50 border-b border-gray-200">
          <div class="py-4 text-center text-sm font-semibold text-red-400">日</div>
          <div class="py-4 text-center text-sm font-semibold text-gray-600">一</div>
          <div class="py-4 text-center text-sm font-semibold text-gray-600">二</div>
          <div class="py-4 text-center text-sm font-semibold text-gray-600">三</div>
          <div class="py-4 text-center text-sm font-semibold text-gray-600">四</div>
          <div class="py-4 text-center text-sm font-semibold text-gray-600">五</div>
          <div class="py-4 text-center text-sm font-semibold text-blue-400">六</div>
        </div>
        <!-- 日历主体 -->
        <div class="grid grid-cols-7">
          <div v-for="(date, idx) in calendarDays" :key="idx"
               :class="dayCellClass(date, idx)"
               @click="handleDateClick(date)">
            <!-- 日期数字 -->
            <div class="flex items-center justify-between mb-2">
              <span :class="dateNumberClass(date, idx)">{{ date.getDate() }}</span>
              <span v-if="getMeetingsForDate(date).length > 0" class="text-xs font-medium text-blue-500 bg-blue-100 px-1.5 py-0.5 rounded-full">
                {{ getMeetingsForDate(date).length }}
              </span>
            </div>
            <!-- 组会列表 -->
            <div class="space-y-1.5 overflow-hidden">
              <div v-for="m in getMeetingsForDate(date).slice(0, 2)" :key="m.id"
                   :class="meetingCardClass(m)"
                   @click.stop="$emit('edit', m)">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-1 min-w-0">
                    <div :class="meetingDotClass(m.meeting_type)" class="w-1.5 h-1.5 rounded-full flex-shrink-0"></div>
                    <span class="font-medium text-gray-700 truncate text-xs">{{ m.title }}</span>
                  </div>
                  <span class="text-gray-400 text-xs flex-shrink-0">{{ formatTime(m.scheduled_at) }}</span>
                </div>
                <div v-if="m.presenters && m.presenters.length" class="flex items-center gap-1 mt-1 text-gray-500">
                  <i class="fa fa-user-o text-xs"></i>
                  <span class="truncate text-xs">{{ presenterNames(m) }}</span>
                </div>
              </div>
              <div v-if="getMeetingsForDate(date).length > 2"
                   class="text-xs text-gray-400 px-2 py-1 bg-gray-50 rounded-lg text-center hover:bg-gray-100 transition-colors">
                +{{ getMeetingsForDate(date).length - 2 }} 更多
              </div>
            </div>
            <!-- hover提示 -->
            <div v-if="getMeetingsForDate(date).length === 0 && isCurrentMonth(date)" class="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
              <span class="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">暂无安排</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 图例 -->
      <div class="mt-6 bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-6">
            <span class="text-sm font-medium text-gray-500">类型标识：</span>
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 rounded-md bg-gradient-to-br from-blue-400 to-blue-600 shadow-sm"></div>
              <span class="text-sm text-gray-600">常规组会</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 rounded-md bg-gradient-to-br from-purple-400 to-purple-600 shadow-sm"></div>
              <span class="text-sm text-gray-600">论文研读</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 rounded-md bg-gradient-to-br from-teal-400 to-teal-600 shadow-sm"></div>
              <span class="text-sm text-gray-600">专题讨论</span>
            </div>
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 rounded-md bg-gradient-to-br from-gray-300 to-gray-400 opacity-60"></div>
              <span class="text-sm text-gray-400">已废弃</span>
            </div>
          </div>
          <div class="text-sm text-gray-400">
            <i class="fa fa-lightbulb-o mr-1"></i>点击日期查看详情
          </div>
        </div>
      </div>
    </div>

    <!-- 侧边面板 -->
    <div class="w-80 space-y-4">
      <!-- 本月概览 -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
            <i class="fa fa-chart-pie text-white text-sm"></i>
          </div>
          <h3 class="text-base font-semibold text-gray-800">本月概览</h3>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-blue-600">{{ monthStats.total }}</div>
            <div class="text-xs text-blue-500 mt-1">组会总数</div>
          </div>
          <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-green-600">{{ monthStats.completed }}</div>
            <div class="text-xs text-green-500 mt-1">已召开</div>
          </div>
          <div class="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-orange-600">{{ monthStats.scheduled }}</div>
            <div class="text-xs text-orange-500 mt-1">待召开</div>
          </div>
          <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 text-center">
            <div class="text-2xl font-bold text-purple-600">{{ monthStats.presenters }}</div>
            <div class="text-xs text-purple-500 mt-1">汇报人次</div>
          </div>
        </div>
      </div>

      <!-- 近期安排 -->
      <div class="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
            <i class="fa fa-clock-o text-white text-sm"></i>
          </div>
          <h3 class="text-base font-semibold text-gray-800">近期安排</h3>
        </div>
        <div class="space-y-3">
          <div v-if="upcomingMeetings.length === 0" class="text-center py-4 text-gray-400">
            <i class="fa fa-calendar-o text-2xl mb-2"></i>
            <p class="text-sm">近期暂无安排</p>
          </div>
          <div v-for="m in upcomingMeetings" :key="m.id"
               class="flex gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
               @click="$emit('edit', m)">
            <div :class="meetingDotClass(m.meeting_type)" class="w-2.5 h-2.5 rounded-full mt-2"></div>
            <div class="flex-1">
              <div class="font-medium text-gray-800 text-sm">{{ m.title }}</div>
              <div class="flex items-center gap-2 mt-1">
                <span class="text-xs text-gray-400">{{ formatDateShort(m.scheduled_at) }} · {{ formatTime(m.scheduled_at) }}</span>
                <span v-if="m.location" :class="locationBadgeClass(m.meeting_type)" class="text-xs px-1.5 py-0.5 rounded-full">{{ m.location }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快速操作 -->
      <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl border border-indigo-100 shadow-sm p-5">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <i class="fa fa-magic text-white text-sm"></i>
          </div>
          <h3 class="text-base font-semibold text-gray-800">快速操作</h3>
        </div>
        <div class="space-y-2">
          <button @click="handleCreateClick" class="w-full py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-all flex items-center justify-center gap-2">
            <i class="fa fa-plus-circle"></i>新建组会
          </button>
          <button @click="$emit('switchView', 'grid')" class="w-full py-2.5 bg-white border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-all flex items-center justify-center gap-2">
            <i class="fa fa-th-large"></i>卡片视图
          </button>
        </div>
      </div>
    </div>

    <!-- 日期详情弹窗 -->
    <div v-if="showPopover"
         class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
         @click.self="closePopover">
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden animate-pop-in">
        <!-- 弹窗头部 -->
        <div class="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <i class="fa fa-calendar text-white text-lg"></i>
            </div>
            <div>
              <h3 class="text-white font-semibold text-lg">{{ popoverDateTitle }}</h3>
              <p class="text-white/70 text-sm">{{ popoverDateFull }}</p>
            </div>
          </div>
          <button @click="closePopover" class="w-8 h-8 rounded-lg bg-white/20 text-white hover:bg-white/30 transition-colors flex items-center justify-center">
            <i class="fa fa-times"></i>
          </button>
        </div>

        <!-- 弹窗内容 -->
        <div class="p-5">
          <!-- 当天组会列表 -->
          <div v-if="popoverMeetings.length" class="space-y-3 mb-5">
            <div v-for="m in popoverMeetings" :key="m.id"
                 :class="popoverMeetingCardClass(m)"
                 class="px-4 py-3 rounded-xl cursor-pointer hover:shadow-md transition-all"
                 @click="$emit('edit', m)">
              <div class="flex items-center gap-3">
                <div :class="meetingIconBg(m.meeting_type)" class="w-8 h-8 rounded-lg flex items-center justify-center">
                  <i :class="meetingIcon(m.meeting_type)" class="text-sm"></i>
                </div>
                <div class="flex-1">
                  <p class="font-medium">{{ m.title }}</p>
                  <p class="text-xs opacity-70">
                    <i class="fa fa-clock-o mr-1"></i>{{ formatTime(m.scheduled_at) }}
                    <i class="fa fa-map-marker ml-2 mr-1"></i>{{ m.location || '地点待定' }}
                  </p>
                </div>
                <span :class="statusBadgeClass(m.status)">{{ statusText(m.status) }}</span>
              </div>
            </div>
          </div>

          <!-- 无组会提示 -->
          <div v-else class="text-center py-6 mb-5">
            <div class="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
              <i class="fa fa-calendar-o text-gray-400 text-2xl"></i>
            </div>
            <p class="text-gray-500">该日期暂无组会安排</p>
          </div>

          <!-- 快捷时间选择 -->
          <div class="mb-4">
            <p class="text-sm text-gray-500 font-medium mb-2">
              <i class="fa fa-clock-o mr-1"></i>快捷选择时间
            </p>
            <div class="grid grid-cols-4 gap-2">
              <button @click="createWithTime('09:00')" class="px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 transition-all">
                <i class="fa fa-sun-o mr-1"></i>9:00
              </button>
              <button @click="createWithTime('14:00')" class="px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 transition-all">
                14:00
              </button>
              <button @click="createWithTime('15:00')" class="px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 hover:text-blue-600 transition-all">
                15:00
              </button>
              <button @click="createWithTime('19:00')" class="px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-600 transition-all">
                <i class="fa fa-moon-o mr-1"></i>19:00
              </button>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="border-t border-gray-100 pt-4 flex gap-3">
            <button @click="closePopover" class="flex-1 py-3 bg-gray-100 text-gray-600 rounded-xl font-medium hover:bg-gray-200 transition-colors">
              <i class="fa fa-times mr-2"></i>关闭
            </button>
            <button @click="createMeetingOnDate" class="flex-1 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-indigo-700 transition-colors shadow-lg">
              <i class="fa fa-plus mr-2"></i>创建组会
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useUserStore } from '../stores/user'

const props = defineProps({
  meetings: Array,
  currentMonth: Date
})
const emit = defineEmits(['prev', 'next', 'today', 'select', 'edit', 'create', 'switchView'])

const userStore = useUserStore()

const typeFilterLocal = ref('')
const statusFilterLocal = ref('')
const showPopover = ref(false)
const popoverDate = ref(null)

const monthTitle = computed(() => {
  return `${props.currentMonth.getFullYear()}年${props.currentMonth.getMonth() + 1}月`
})

const popoverDateTitle = computed(() => {
  if (!popoverDate.value) return ''
  const d = popoverDate.value
  const weekDay = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  return `${d.getMonth() + 1}月${d.getDate()}日 ${weekDay}`
})

const popoverDateFull = computed(() => {
  if (!popoverDate.value) return ''
  const d = popoverDate.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const popoverMeetings = computed(() => {
  if (!popoverDate.value) return []
  return getMeetingsForDate(popoverDate.value)
})

// 过滤后的会议列表
const filteredMeetings = computed(() => {
  return props.meetings.filter(m => {
    if (typeFilterLocal.value && m.meeting_type !== typeFilterLocal.value) return false
    if (statusFilterLocal.value && m.status !== statusFilterLocal.value) return false
    return true
  })
})

// 本月统计
const monthStats = computed(() => {
  const currentMonthMeetings = filteredMeetings.value.filter(m => {
    if (!m.scheduled_at) return false
    const d = new Date(m.scheduled_at)
    return d.getMonth() === props.currentMonth.getMonth() && d.getFullYear() === props.currentMonth.getFullYear()
  })

  return {
    total: currentMonthMeetings.length,
    completed: currentMonthMeetings.filter(m => m.status === 'completed').length,
    scheduled: currentMonthMeetings.filter(m => m.status === 'scheduled').length,
    presenters: currentMonthMeetings.reduce((sum, m) => sum + (m.presenters?.length || 0), 0)
  }
})

// 近期安排（未来7天）
const upcomingMeetings = computed(() => {
  const now = new Date()
  const futureDate = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)

  return filteredMeetings.value
    .filter(m => {
      if (!m.scheduled_at) return false
      const d = new Date(m.scheduled_at)
      return d >= now && d <= futureDate && m.status === 'scheduled'
    })
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
    .slice(0, 4)
})

const calendarDays = computed(() => {
  const year = props.currentMonth.getFullYear()
  const month = props.currentMonth.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const days = []

  // 上月的填充天数
  for (let i = 0; i < firstDay.getDay(); i++) {
    days.push(new Date(year, month, -firstDay.getDay() + i + 1))
  }

  // 当月的天数
  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push(new Date(year, month, i))
  }

  // 下月的填充天数（补齐到42天，6周）
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    days.push(new Date(year, month + 1, i))
  }

  return days
})

function isCurrentMonth(date) {
  return date.getMonth() === props.currentMonth.getMonth()
}

function handleDateClick(date) {
  popoverDate.value = date
  showPopover.value = true
}

function closePopover() {
  showPopover.value = false
  popoverDate.value = null
}

function handleCreateClick() {
  if (userStore.role !== 'admin' && userStore.role !== 'teacher') {
    window.$toast?.('只有导师和管理员可以创建组会', 'warning')
    return
  }
  emit('create', new Date())
}

function createMeetingOnDate() {
  if (popoverDate.value) {
    emit('create', popoverDate.value)
    closePopover()
  }
}

function createWithTime(time) {
  if (popoverDate.value) {
    emit('create', popoverDate.value, time)
    closePopover()
  }
}

function dayCellClass(date, idx) {
  const today = new Date()
  const isToday = date.toDateString() === today.toDateString()
  const isCurMonth = isCurrentMonth(date)
  const hasMeetings = getMeetingsForDate(date).length > 0
  const isWeekendDay = idx % 7 === 0 || idx % 7 === 6
  const weekendBg = idx % 7 === 0 ? 'bg-red-50/30' : 'bg-blue-50/30'

  return [
    'min-h-[120px] p-3 border-b border-r border-gray-100 cursor-pointer relative group',
    isToday ? 'bg-gradient-to-br from-blue-100 to-indigo-100' : '',
    !isToday && hasMeetings && isCurMonth ? 'bg-white' : '',
    !isToday && !hasMeetings && isCurMonth && isWeekendDay ? weekendBg : '',
    !isToday && !hasMeetings && isCurMonth && !isWeekendDay ? 'bg-white' : '',
    !isCurMonth ? 'bg-gray-100/50' : '',
    isCurMonth ? 'hover:shadow-md hover:bg-gradient-to-br hover:from-blue-50 hover:to-indigo-50 transition-all duration-200' : ''
  ]
}

function dateNumberClass(date, idx) {
  const today = new Date()
  const isToday = date.toDateString() === today.toDateString()
  const isCurMonth = isCurrentMonth(date)
  const hasMeetings = getMeetingsForDate(date).length > 0
  const isWeekendDay = idx % 7 === 0 || idx % 7 === 6

  return [
    isToday ? 'w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center text-sm font-bold shadow-lg' : '',
    !isToday && isCurMonth && hasMeetings ? 'text-sm font-semibold text-gray-800' : '',
    !isToday && isCurMonth && !hasMeetings && isWeekendDay ? 'text-sm text-gray-400' : '',
    !isToday && isCurMonth && !hasMeetings && !isWeekendDay ? 'text-sm text-gray-400 group-hover:text-gray-600' : '',
    !isCurMonth ? 'text-sm text-gray-300' : ''
  ]
}

function getMeetingsForDate(date) {
  const dateKey = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
  return filteredMeetings.value.filter(m => {
    if (!m.scheduled_at) return false
    const meetingDate = new Date(m.scheduled_at)
    const meetingKey = `${meetingDate.getFullYear()}-${String(meetingDate.getMonth()+1).padStart(2,'0')}-${String(meetingDate.getDate()).padStart(2,'0')}`
    return meetingKey === dateKey
  })
}

function meetingCardClass(m) {
  const typeBgMap = {
    regular: 'bg-gradient-to-r from-blue-50 to-blue-100 border-blue-300',
    paper_reading: 'bg-gradient-to-r from-purple-50 to-purple-100 border-purple-300',
    discussion: 'bg-gradient-to-r from-teal-50 to-teal-100 border-teal-300'
  }
  const statusExtra = m.status === 'cancelled' ? 'opacity-40' : ''

  return [
    typeBgMap[m.meeting_type] || 'bg-gradient-to-r from-gray-50 to-gray-100 border-gray-300',
    statusExtra,
    'text-xs px-2.5 py-1.5 rounded-lg border-l-3 shadow-sm hover:shadow-md transition-shadow'
  ]
}

function popoverMeetingCardClass(m) {
  const typeBgMap = {
    regular: 'bg-gradient-to-r from-blue-50 to-blue-100',
    paper_reading: 'bg-gradient-to-r from-purple-50 to-purple-100',
    discussion: 'bg-gradient-to-r from-teal-50 to-teal-100'
  }
  return typeBgMap[m.meeting_type] || 'bg-gradient-to-r from-gray-50 to-gray-100'
}

function meetingDotClass(type) {
  const map = {
    regular: 'bg-gradient-to-br from-blue-400 to-blue-600',
    paper_reading: 'bg-gradient-to-br from-purple-400 to-purple-600',
    discussion: 'bg-gradient-to-br from-teal-400 to-teal-600'
  }
  return map[type] || 'bg-gradient-to-br from-gray-400 to-gray-600'
}

function meetingIcon(type) {
  const map = {
    regular: 'fa fa-users',
    paper_reading: 'fa fa-book',
    discussion: 'fa fa-lightbulb-o'
  }
  return map[type] || 'fa fa-calendar'
}

function meetingIconBg(type) {
  const map = {
    regular: 'bg-blue-100 text-blue-600',
    paper_reading: 'bg-purple-100 text-purple-600',
    discussion: 'bg-teal-100 text-teal-600'
  }
  return map[type] || 'bg-gray-100 text-gray-600'
}

function locationBadgeClass(type) {
  const map = {
    regular: 'bg-blue-100 text-blue-600',
    paper_reading: 'bg-purple-100 text-purple-600',
    discussion: 'bg-teal-100 text-teal-600'
  }
  return map[type] || 'bg-gray-100 text-gray-600'
}

function statusText(status) {
  const map = { scheduled: '待召开', ongoing: '进行中', completed: '已召开', cancelled: '已废弃' }
  return map[status] || status
}

function statusBadgeClass(status) {
  const map = {
    scheduled: 'px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-700',
    ongoing: 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-700',
    completed: 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600',
    cancelled: 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-700'
  }
  return map[status] || 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600'
}

function presenterNames(m) {
  if (!m.presenters || m.presenters.length === 0) return ''
  const names = m.presenters.slice(0, 2).map(p => p.real_name || p.username).join('、')
  return m.presenters.length > 2 ? `${names}+${m.presenters.length - 2}` : names
}

function formatTime(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}

function formatDateShort(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${date.getMonth()+1}月${date.getDate()}日`
}
</script>

<style scoped>
.animate-pop-in {
  animation: popIn 0.3s ease-out;
}
@keyframes popIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
.border-l-3 {
  border-left-width: 3px;
}
</style>