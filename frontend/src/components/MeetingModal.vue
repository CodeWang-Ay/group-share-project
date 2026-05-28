<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
      <!-- 弹窗头部 -->
      <div class="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
            <i class="fa fa-calendar-plus-o text-white text-lg"></i>
          </div>
          <h3 class="text-white font-semibold text-lg">{{ mode === 'edit' ? '编辑组会' : '新建组会' }}</h3>
        </div>
        <button @click="$emit('close')" class="w-8 h-8 rounded-lg bg-white/20 text-white hover:bg-white/30 transition-colors flex items-center justify-center">
          <i class="fa fa-times"></i>
        </button>
      </div>

      <!-- 表单内容 -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-5">
        <!-- 组会标题 -->
        <div>
          <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <i class="fa fa-edit text-blue-500"></i>
            组会标题 <span class="text-red-500">*</span>
          </label>
          <input v-model="form.title" type="text" required
                 class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                 placeholder="请输入组会标题">
        </div>

        <!-- 组会类型 -->
        <div>
          <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <i class="fa fa-tag text-purple-500"></i>
            组会类型 <span class="text-red-500">*</span>
          </label>
          <div class="grid grid-cols-3 gap-3">
            <button type="button" @click="form.meeting_type = 'regular'"
                    :class="typeBtnClass('regular')">
              <i class="fa fa-users mr-1"></i>常规组会
            </button>
            <button type="button" @click="form.meeting_type = 'paper_reading'"
                    :class="typeBtnClass('paper_reading')">
              <i class="fa fa-book mr-1"></i>论文研读
            </button>
            <button type="button" @click="form.meeting_type = 'discussion'"
                    :class="typeBtnClass('discussion')">
              <i class="fa fa-lightbulb-o mr-1"></i>专题讨论
            </button>
          </div>
        </div>

        <!-- 时间和地点 -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <i class="fa fa-clock-o text-teal-500"></i>
              时间 <span class="text-red-500">*</span>
            </label>
            <input v-model="form.scheduled_at" type="datetime-local" required
                   class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all">
          </div>
          <div>
            <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
              <i class="fa fa-map-marker text-red-500"></i>
              地点
            </label>
            <input v-model="form.location" type="text"
                   class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                   placeholder="会议室或线上链接">
          </div>
        </div>

        <!-- 描述 -->
        <div>
          <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <i class="fa fa-file-text-o text-gray-500"></i>
            描述
          </label>
          <textarea v-model="form.description" rows="3"
                    class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all resize-none"
                    placeholder="组会内容简介"></textarea>
        </div>

        <!-- 汇报人（支持搜索选择） -->
        <div>
          <label class="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
            <i class="fa fa-user-circle-o text-indigo-500"></i>
            汇报人
          </label>

          <!-- 已选汇报人列表 -->
          <div v-if="form.presenters.length" class="flex flex-wrap gap-2 mb-3">
            <span v-for="(p, idx) in form.presenters" :key="p.id || idx"
                  class="inline-flex items-center gap-2 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 px-3 py-2 rounded-xl">
              <img v-if="p.avatar" :src="p.avatar" class="w-5 h-5 rounded-full">
              <i v-else class="fa fa-user-o text-xs"></i>
              <span class="font-medium">{{ p.username }}</span>
              <button @click="removePresenter(idx)" type="button"
                      class="w-5 h-5 rounded-full bg-blue-500/20 hover:bg-red-500 hover:text-white flex items-center justify-center transition-colors">
                <i class="fa fa-times text-xs"></i>
              </button>
            </span>
          </div>

          <!-- 搜索输入框 -->
          <div class="relative">
            <div class="flex gap-2">
              <div class="relative flex-1">
                <input v-model="searchKeyword" @input="handleSearch" @focus="showDropdown = true"
                       type="text"
                       class="w-full border-2 border-gray-200 rounded-xl px-4 py-3 pl-10 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
                       placeholder="搜索成员姓名...">
                <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
              </div>
              <button @click="showDropdown = !showDropdown" type="button"
                      class="px-4 py-3 bg-gray-100 text-gray-600 rounded-xl hover:bg-gray-200 transition-colors">
                <i class="fa fa-chevron-down"></i>
              </button>
            </div>

            <!-- 搜索下拉列表 -->
            <div v-if="showDropdown && filteredMembers.length"
                 class="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-100 max-h-48 overflow-y-auto z-10">
              <div v-for="member in filteredMembers" :key="member.id"
                   @click="addPresenter(member)"
                   class="px-4 py-3 hover:bg-blue-50 cursor-pointer flex items-center gap-3 transition-colors border-b border-gray-50 last:border-0">
                <img :src="member.avatar || `https://picsum.photos/id/${member.id}/200/200`"
                     class="w-8 h-8 rounded-full object-cover">
                <div class="flex-1">
                  <p class="font-medium text-gray-800">{{ member.username }}</p>
                  <p class="text-xs text-gray-500">{{ member.role === 'teacher' ? '导师' : member.role === 'admin' ? '管理员' : '学生' }}</p>
                </div>
                <i class="fa fa-plus-circle text-blue-500"></i>
              </div>
            </div>

            <!-- 无搜索结果 -->
            <div v-if="showDropdown && searchKeyword && filteredMembers.length === 0"
                 class="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-100 p-4 text-center text-gray-500">
              <i class="fa fa-user-times text-2xl mb-2"></i>
              <p>未找到匹配的成员</p>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">
            <i class="fa fa-info-circle mr-1"></i>搜索并选择团队成员作为汇报人
          </p>
        </div>

        <!-- 操作按钮 -->
        <div class="border-t border-gray-100 pt-4 flex gap-3">
          <button type="button" @click="$emit('close')"
                  class="flex-1 py-3 bg-gray-100 text-gray-600 rounded-xl font-medium hover:bg-gray-200 transition-colors flex items-center justify-center gap-2">
            <i class="fa fa-times"></i>
            <span>取消</span>
          </button>
          <button type="submit"
                  class="flex-1 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-medium hover:from-blue-600 hover:to-indigo-700 transition-colors shadow-lg flex items-center justify-center gap-2">
            <i class="fa fa-check"></i>
            <span>{{ mode === 'edit' ? '保存修改' : '创建组会' }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { meetingApi } from '../api/meeting'

const props = defineProps({
  meeting: Object,
  mode: String,
  presetDateTime: String
})
const emit = defineEmits(['close', 'save'])

const form = reactive({
  title: '',
  meeting_type: 'regular',
  scheduled_at: '',
  location: '',
  description: '',
  presenters: []
})

const searchKeyword = ref('')
const showDropdown = ref(false)
const allMembers = ref([])
const loading = ref(false)

const typeBtnClass = computed(() => (type) => [
  'py-3 px-4 rounded-xl border-2 font-medium transition-all flex items-center justify-center',
  form.meeting_type === type
    ? type === 'regular' ? 'bg-blue-500 text-white border-blue-500 shadow-lg'
      : type === 'paper_reading' ? 'bg-purple-500 text-white border-purple-500 shadow-lg'
      : 'bg-teal-500 text-white border-teal-500 shadow-lg'
    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
])

const filteredMembers = computed(() => {
  if (!searchKeyword.value) return allMembers.value
  const keyword = searchKeyword.value.toLowerCase()
  return allMembers.value.filter(m =>
    m.username?.toLowerCase().includes(keyword) ||
    m.real_name?.toLowerCase().includes(keyword)
  )
})

// 加载成员列表
async function loadMembers() {
  if (allMembers.value.length) return
  loading.value = true
  try {
    const res = await meetingApi.searchMembers('')
    if (res.data.success) {
      allMembers.value = res.data.data.members || []
    }
  } catch (e) {
    console.error('加载成员失败:', e)
  }
  loading.value = false
}

function handleSearch() {
  if (!allMembers.value.length) {
    loadMembers()
  }
}

function addPresenter(member) {
  // 检查是否已添加
  const exists = form.presenters.some(p => p.id === member.id)
  if (!exists) {
    form.presenters.push({
      id: member.id,
      username: member.username,
      avatar: member.avatar
    })
  }
  searchKeyword.value = ''
  showDropdown.value = false
}

function removePresenter(idx) {
  form.presenters.splice(idx, 1)
}

onMounted(() => {
  loadMembers()

  if (props.mode === 'edit' && props.meeting) {
    form.title = props.meeting.title || ''
    form.meeting_type = props.meeting.meeting_type || 'regular'
    form.scheduled_at = formatDateTimeLocal(props.meeting.scheduled_at)
    form.location = props.meeting.location || ''
    form.description = props.meeting.description || ''
    form.presenters = (props.meeting.presenters || []).map(p => ({
      id: p.user_id || p.id,
      username: p.username,
      avatar: p.avatar
    }))
  } else if (props.presetDateTime) {
    form.scheduled_at = props.presetDateTime
  }
})

function formatDateTimeLocal(d) {
  if (!d) return ''
  const date = new Date(d)
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}T${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`
}

function handleSubmit() {
  emit('save', {
    title: form.title,
    meeting_type: form.meeting_type,
    scheduled_at: form.scheduled_at,
    location: form.location,
    description: form.description,
    presenter_ids: form.presenters.map(p => p.id)
  })
}

// 点击外部关闭下拉框
watch(showDropdown, (val) => {
  if (val) {
    document.addEventListener('click', closeDropdownOutside)
  } else {
    document.removeEventListener('click', closeDropdownOutside)
  }
})

function closeDropdownOutside(e) {
  const target = e.target
  if (!target.closest('.relative')) {
    showDropdown.value = false
  }
}
</script>