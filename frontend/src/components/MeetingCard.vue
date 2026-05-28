<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md hover:-translate-y-1">
    <div v-if="loading" class="p-6 text-center text-gray-500">
      <i class="fa fa-spinner fa-spin text-4xl mb-3"></i>
      <p>加载中...</p>
    </div>
    <div v-else-if="!meeting" class="p-6 text-center text-gray-500">
      <i class="fa fa-calendar-o text-4xl mb-3"></i>
      <p>暂无即将到来的组会</p>
      <a href="/gm_meeting_schedule" class="text-primary hover:underline mt-2 block">安排新组会</a>
    </div>
    <template v-else>
      <div class="p-6 border-b bg-gradient-to-r from-primary/5 to-primary/10">
        <div class="flex flex-col lg:flex-row lg:justify-between gap-4">
          <div>
            <span class="inline-block px-3 py-1 bg-primary text-white text-sm rounded-full mb-3">{{ typeText }}</span>
            <h3 class="text-lg lg:text-xl font-bold">{{ meeting.title }}</h3>
            <p class="text-gray-600 mt-1">{{ meeting.description || '暂无描述' }}</p>
          </div>
          <div class="lg:text-right">
            <p class="text-gray-500 text-sm">日期时间</p>
            <p class="font-medium flex items-center gap-1 mt-1 lg:justify-end">
              <i class="fa fa-calendar text-primary"></i> {{ formattedDate }}（{{ weekDay }}）{{ formattedTime }}
            </p>
            <p class="font-medium flex items-center gap-1 mt-2 lg:justify-end">
              <i class="fa fa-map-marker text-primary"></i> {{ meeting.location || '地点待定' }}
            </p>
          </div>
        </div>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
              <i class="fa fa-user-circle-o text-primary"></i> 汇报人 ({{ presentersCount }}人)
            </h4>
            <div class="flex flex-wrap gap-2">
              <template v-for="p in presenters.slice(0, 3)" :key="p.id">
                <div class="flex items-center gap-1 bg-gray-100 px-3 py-1 rounded-full text-sm">
                  <div class="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">
                    <i class="fa fa-user"></i>
                  </div>
                  {{ p.username || '未知' }}
                </div>
              </template>
              <span v-if="!presentersCount" class="text-gray-400 text-sm">暂无汇报人</span>
            </div>
          </div>
          <div>
            <h4 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
              <i class="fa fa-file-text-o text-primary"></i> 材料提交
            </h4>
            <p class="text-sm">
              已提交 {{ materialsSubmitted }}/{{ materialsTotal }}
              <span v-if="materialsSubmitted === materialsTotal" class="ml-2 text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">全部完成</span>
              <span v-else class="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">部分完成</span>
            </p>
          </div>
          <div>
            <h4 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
              <i class="fa fa-info-circle text-primary"></i> 组会状态
            </h4>
            <p class="text-sm">{{ statusText }}</p>
          </div>
        </div>
        <div class="mt-6 flex flex-col sm:flex-row gap-3 sm:justify-end">
          <a href="/gm_meeting_schedule" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-center">
            <i class="fa fa-list mr-1"></i> 查看全部组会
          </a>
          <a :href="`/gm_meeting_schedule?id=${meeting.id}`" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 text-center">
            <i class="fa fa-eye mr-1"></i> 查看详情
          </a>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  meeting: Object,
  loading: { type: Boolean, default: false }
})

const typeText = computed(() => {
  const map = { regular: '常规组会', paper_reading: '论文研读', discussion: '专题讨论' }
  return map[props.meeting?.meeting_type] || '组会'
})

const presenters = computed(() => props.meeting?.presenters || [])
const presentersCount = computed(() => presenters.value.length)

const materialsStatus = computed(() => props.meeting?.materials_status || { submitted: 0, total: 0 })
const materialsSubmitted = computed(() => materialsStatus.value.submitted)
const materialsTotal = computed(() => materialsStatus.value.total)

const statusText = computed(() => {
  const map = { scheduled: '待召开', ongoing: '进行中', completed: '已召开', cancelled: '已取消' }
  return map[props.meeting?.status] || '未知'
})

const date = computed(() => props.meeting?.scheduled_at ? new Date(props.meeting.scheduled_at) : null)

const formattedDate = computed(() => {
  if (!date.value) return ''
  return `${date.value.getFullYear()}-${String(date.value.getMonth()+1).padStart(2,'0')}-${String(date.value.getDate()).padStart(2,'0')}`
})

const formattedTime = computed(() => {
  if (!date.value) return ''
  return `${String(date.value.getHours()).padStart(2,'0')}:${String(date.value.getMinutes()).padStart(2,'0')}`
})

const weekDay = computed(() => {
  if (!date.value) return ''
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[date.value.getDay()]
})
</script>