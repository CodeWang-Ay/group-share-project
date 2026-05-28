<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden relative">
    <!-- 日历头部 -->
    <div class="bg-gradient-to-r from-primary/5 to-primary/10 px-6 py-4 border-b border-gray-100">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-3">
          <button @click="$emit('prev')" class="w-10 h-10 rounded-full bg-white shadow-sm border border-gray-200 flex items-center justify-center hover:bg-gray-50 hover:shadow transition-all">
            <i class="fa fa-chevron-left text-gray-600"></i>
          </button>
          <div class="text-center">
            <h3 class="text-xl font-bold text-gray-800">{{ monthTitle }}</h3>
            <p class="text-sm text-gray-500">{{ meetingCount }}场组会</p>
          </div>
          <button @click="$emit('next')" class="w-10 h-10 rounded-full bg-white shadow-sm border border-gray-200 flex items-center justify-center hover:bg-gray-50 hover:shadow transition-all">
            <i class="fa fa-chevron-right text-gray-600"></i>
          </button>
        </div>
        <div class="flex gap-2">
          <button @click="$emit('today')" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2">
            <i class="fa fa-crosshairs"></i>
            <span>今天</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="px-6 py-3 bg-gray-50 border-b border-gray-100 flex gap-6">
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-blue-500"></div>
        <span class="text-sm text-gray-600">常规组会 {{ typeCounts.regular }}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-purple-500"></div>
        <span class="text-sm text-gray-600">论文研读 {{ typeCounts.paper_reading }}</span>
      </div>
      <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-full bg-teal-500"></div>
        <span class="text-sm text-gray-600">专题讨论 {{ typeCounts.discussion }}</span>
      </div>
    </div>

    <!-- 星期标题 -->
    <div class="grid grid-cols-7 border-b border-gray-100">
      <div v-for="(day, idx) in weekDays" :key="idx"
           :class="['text-center py-3 text-sm font-medium', idx === 0 || idx === 6 ? 'text-red-400 bg-red-50/50' : 'text-gray-600 bg-gray-50']">
        {{ day }}
      </div>
    </div>

    <!-- 日历格子 -->
    <div class="grid grid-cols-7 relative">
      <div v-for="(date, idx) in calendarDays" :key="idx"
           :class="dayCellClass(date, idx)"
           @click="handleDateClick(date, $event)">
        <!-- 日期数字 -->
        <div class="flex items-center justify-center mb-1">
          <span :class="dateNumberClass(date, idx)">
            {{ date.getDate() }}
          </span>
        </div>

        <!-- 组会事件 -->
        <div v-if="getMeetingsForDate(date).length" class="space-y-1 px-1">
          <div v-for="m in getMeetingsForDate(date).slice(0, 2)" :key="m.id"
               :class="meetingCardClass(m.meeting_type, m.status)"
               class="text-xs px-2 py-1 rounded-md truncate flex items-center gap-1">
            <i :class="meetingIcon(m.meeting_type)" class="text-xs"></i>
            <span class="truncate">{{ m.title }}</span>
          </div>
          <div v-if="getMeetingsForDate(date).length > 2"
               class="text-xs text-center py-1 text-gray-500 bg-gray-100 rounded">
            +{{ getMeetingsForDate(date).length - 2 }} 更多
          </div>
        </div>
      </div>

      <!-- 点击日期后的弹出菜单 -->
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
              <p class="text-sm text-gray-500 font-medium mb-2">
                <i class="fa fa-list-ul mr-1"></i>当天组会
              </p>
              <div v-for="m in popoverMeetings" :key="m.id"
                   :class="meetingCardClass(m.meeting_type, m.status)"
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
                  <i class="fa fa-cloud mr-1"></i>14:00
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
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  meetings: Array,
  currentMonth: Date
})
const emit = defineEmits(['prev', 'next', 'today', 'select', 'edit', 'create'])

const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

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

const meetingCount = computed(() => {
  return props.meetings.filter(m => {
    if (!m.scheduled_at) return false
    const d = new Date(m.scheduled_at)
    return d.getMonth() === props.currentMonth.getMonth() && d.getFullYear() === props.currentMonth.getFullYear()
  }).length
})

const typeCounts = computed(() => {
  const counts = { regular: 0, paper_reading: 0, discussion: 0 }
  props.meetings.forEach(m => {
    if (m.scheduled_at) {
      const d = new Date(m.scheduled_at)
      if (d.getMonth() === props.currentMonth.getMonth() && d.getFullYear() === props.currentMonth.getFullYear()) {
        counts[m.meeting_type] = (counts[m.meeting_type] || 0) + 1
      }
    }
  })
  return counts
})

const calendarDays = computed(() => {
  const year = props.currentMonth.getFullYear()
  const month = props.currentMonth.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const days = []

  for (let i = 0; i < firstDay.getDay(); i++) {
    days.push(new Date(year, month, -firstDay.getDay() + i + 1))
  }

  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push(new Date(year, month, i))
  }

  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    days.push(new Date(year, month + 1, i))
  }

  return days
})

function handleDateClick(date, event) {
  const isCurrentMonth = date.getMonth() === props.currentMonth.getMonth()
  if (!isCurrentMonth) {
    emit('select', date)
    return
  }

  popoverDate.value = date
  showPopover.value = true
}

function closePopover() {
  showPopover.value = false
  popoverDate.value = null
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

function isWeekend(idx) {
  return idx % 7 === 0 || idx % 7 === 6
}

function dayCellClass(date, idx) {
  const today = new Date()
  const isToday = date.toDateString() === today.toDateString()
  const isCurrentMonth = date.getMonth() === props.currentMonth.getMonth()
  const hasMeetings = getMeetingsForDate(date).length > 0
  const isSelected = popoverDate.value && date.toDateString() === popoverDate.value.toDateString()

  return [
    'min-h-[80px] p-2 border-b border-r border-gray-100 cursor-pointer transition-all relative',
    isToday ? 'bg-primary/5 ring-2 ring-primary/30 ring-inset' : '',
    isSelected ? 'bg-primary/10' : '',
    isWeekend(idx) && isCurrentMonth ? 'bg-red-50/30' : '',
    !isCurrentMonth ? 'bg-gray-50/50 text-gray-400' : '',
    hasMeetings && isCurrentMonth ? 'hover:bg-blue-50/50' : 'hover:bg-gray-50',
    isCurrentMonth && !isToday && !isSelected ? 'bg-white' : ''
  ]
}

function dateNumberClass(date, idx) {
  const today = new Date()
  const isToday = date.toDateString() === today.toDateString()
  const isCurrentMonth = date.getMonth() === props.currentMonth.getMonth()
  const isWeekendDay = isWeekend(idx)

  return [
    'w-7 h-7 flex items-center justify-center rounded-full text-sm font-medium',
    isToday ? 'bg-primary text-white shadow-sm' : '',
    !isToday && isCurrentMonth && isWeekendDay ? 'text-red-600 font-semibold' : '',
    !isToday && isCurrentMonth && !isWeekendDay ? 'text-gray-800 font-medium' : '',
    !isCurrentMonth ? 'text-gray-300 font-normal' : ''
  ]
}

function getMeetingsForDate(date) {
  const dateKey = `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
  return props.meetings.filter(m => {
    if (!m.scheduled_at) return false
    const meetingDate = new Date(m.scheduled_at)
    const meetingKey = `${meetingDate.getFullYear()}-${String(meetingDate.getMonth()+1).padStart(2,'0')}-${String(meetingDate.getDate()).padStart(2,'0')}`
    return meetingKey === dateKey
  })
}

function meetingCardClass(type, status) {
  const baseClasses = {
    regular: 'bg-gradient-to-r from-blue-100 to-blue-50 text-blue-700 border-l-2 border-blue-500',
    paper_reading: 'bg-gradient-to-r from-purple-100 to-purple-50 text-purple-700 border-l-2 border-purple-500',
    discussion: 'bg-gradient-to-r from-teal-100 to-teal-50 text-teal-700 border-l-2 border-teal-500'
  }

  if (status === 'completed') {
    return (baseClasses[type] || 'bg-gradient-to-r from-gray-100 to-gray-50 text-gray-600 border-l-2 border-gray-400') + ' opacity-60'
  }

  return baseClasses[type] || 'bg-gradient-to-r from-gray-100 to-gray-50 text-gray-700 border-l-2 border-gray-400'
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

function statusText(status) {
  const map = { scheduled: '待召开', ongoing: '进行中', completed: '已召开', cancelled: '已取消' }
  return map[status] || status
}

function statusBadgeClass(status) {
  const map = {
    scheduled: 'px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700',
    ongoing: 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-700',
    completed: 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600',
    cancelled: 'px-2 py-1 text-xs rounded-full bg-red-100 text-red-700'
  }
  return map[status] || 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600'
}

function formatTime(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
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
</style>