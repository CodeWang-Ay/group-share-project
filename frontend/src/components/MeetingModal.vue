<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 overflow-hidden flex flex-col max-h-[85vh]">
      <!-- 头部 -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
        <h2 class="text-lg font-semibold text-gray-800">{{ mode === 'edit' ? '编辑组会' : '新建组会' }}</h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>

      <!-- 表单内容 -->
      <div class="p-6 overflow-y-auto flex-1">
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- 组会标题 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">组会标题 <span class="text-red-500">*</span></label>
            <input v-model="form.title" type="text" required
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                   placeholder="第XX周组会 - 论文研读与进展汇报">
            <p class="text-xs text-gray-400 mt-1">提示：建议使用"第XX周组会 - 主题"格式</p>
          </div>

          <!-- 组会类型和总时长 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">组会类型</label>
              <select v-model="form.meeting_type"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary">
                <option value="regular">常规组会</option>
                <option value="paper_reading">论文研读</option>
                <option value="discussion">专题讨论</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">总时长（分钟）</label>
              <input v-model.number="form.duration_total" type="number" min="15" max="180"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary">
            </div>
          </div>

          <!-- 会议时间和地点 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">会议时间 <span class="text-red-500">*</span></label>
              <input v-model="form.scheduled_at" type="datetime-local" required
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">会议地点</label>
              <input v-model="form.location" type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                     placeholder="例如：计算中心302会议室">
            </div>
          </div>

          <!-- 线上会议 -->
          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="form.is_online" type="checkbox" class="rounded border-gray-300 text-primary focus:ring-primary">
              <span class="text-sm text-gray-700">线上会议</span>
            </label>
            <div v-if="form.is_online" class="flex-1">
              <input v-model="form.online_link" type="text"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                     placeholder="线上会议链接">
            </div>
          </div>

          <!-- 组会描述 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">组会描述</label>
            <textarea v-model="form.description" rows="3"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none"
                      placeholder="组会主题说明"></textarea>
          </div>

          <!-- 需要提交材料 -->
          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input v-model="form.material_required" type="checkbox" class="rounded border-gray-300 text-primary focus:ring-primary">
              <span class="text-sm text-gray-700">需要提交材料</span>
            </label>
          </div>

          <!-- 组会状态（仅编辑模式显示） -->
          <div v-if="mode === 'edit'">
            <label class="block text-sm font-medium text-gray-700 mb-1">组会状态</label>
            <select v-model="form.status"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary">
              <option value="scheduled">待召开</option>
              <option value="ongoing">进行中</option>
              <option value="completed">已召开</option>
              <option value="cancelled">已废弃</option>
              <option value="postponed">已推迟</option>
            </select>
          </div>

          <!-- 备注 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">备注</label>
            <textarea v-model="form.notes" rows="2"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none"
                      placeholder="例如：请各位汇报人提前提交PPT"></textarea>
          </div>

          <!-- 汇报人选择 -->
          <div class="border-t border-gray-200 pt-4 mt-4">
            <div class="flex justify-between items-center mb-3">
              <label class="block text-sm font-medium text-gray-700">汇报人</label>
              <button type="button" @click="showPresenterModal = true" class="text-sm text-primary hover:text-primary/80 flex items-center gap-1">
                <i class="fa fa-plus"></i> 添加汇报人
              </button>
            </div>
            <div class="space-y-2 max-h-40 overflow-y-auto">
              <div v-if="form.presenters.length === 0" class="text-sm text-gray-400">
                暂无汇报人，点击上方按钮添加
              </div>
              <div v-for="(p, idx) in form.presenters" :key="p.id || idx"
                   class="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                  <img :src="getAvatarUrl(p.avatar, p.username)" class="w-8 h-8 rounded-full object-cover">
                  <div>
                    <p class="font-medium text-gray-800">{{ p.real_name || p.username }}</p>
                    <p class="text-xs text-gray-500">{{ p.degree_type || '' }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <input v-model.number="p.duration" type="number" min="5" max="60" placeholder="时长"
                         class="w-20 px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50">
                  <span class="text-xs text-gray-500">分钟</span>
                  <button @click="removePresenter(idx)" type="button"
                          class="w-6 h-6 rounded-full bg-red-100 text-red-500 hover:bg-red-200 flex items-center justify-center transition-colors">
                    <i class="fa fa-times text-xs"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>

      <!-- 底部按钮 -->
      <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 flex-shrink-0 bg-white">
        <button @click="close" type="button" class="px-4 py-2 border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          取消
        </button>
        <button @click="handleSubmit" type="button" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
          {{ mode === 'edit' ? '保存修改' : '创建组会' }}
        </button>
      </div>

      <!-- 汇报人选择弹窗 -->
      <PresenterSelectModal v-model="showPresenterModal" :selected-ids="selectedPresenterIds" @select="addPresenters" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { getAvatarUrl } from '../config'
import PresenterSelectModal from './PresenterSelectModal.vue'

const props = defineProps({
  meeting: Object,
  mode: String,
  presetDateTime: String
})
const emit = defineEmits(['close', 'save'])

const showPresenterModal = ref(false)

const form = reactive({
  title: '',
  meeting_type: 'regular',
  duration_total: 60,
  scheduled_at: '',
  location: '',
  is_online: false,
  online_link: '',
  description: '',
  material_required: true,
  status: 'scheduled',
  notes: '',
  presenters: []
})

const selectedPresenterIds = computed(() => form.presenters.map(p => p.id))

onMounted(() => {
  if (props.mode === 'edit' && props.meeting) {
    form.title = props.meeting.title || ''
    form.meeting_type = props.meeting.meeting_type || 'regular'
    form.duration_total = props.meeting.duration_total || 60
    form.scheduled_at = formatDateTimeLocal(props.meeting.scheduled_at)
    form.location = props.meeting.location || ''
    form.is_online = props.meeting.is_online || false
    form.online_link = props.meeting.online_link || ''
    form.description = props.meeting.description || ''
    form.material_required = props.meeting.material_required ?? true
    form.status = props.meeting.status || 'scheduled'
    form.notes = props.meeting.notes || ''
    form.presenters = (props.meeting.presenters || []).map(p => ({
      id: p.user_id || p.id,
      username: p.username,
      real_name: p.real_name,
      avatar: p.avatar,
      degree_type: p.degree_type,
      duration: p.duration || 15
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

function addPresenters(members) {
  members.forEach(m => {
    const exists = form.presenters.some(p => p.id === m.id)
    if (!exists) {
      form.presenters.push({
        id: m.id,
        username: m.username,
        real_name: m.real_name,
        avatar: m.avatar,
        degree_type: m.degree_type,
        duration: 15
      })
    }
  })
  showPresenterModal.value = false
}

function removePresenter(idx) {
  form.presenters.splice(idx, 1)
}

function handleSubmit() {
  emit('save', {
    title: form.title,
    meeting_type: form.meeting_type,
    duration_total: form.duration_total,
    scheduled_at: form.scheduled_at,
    location: form.location,
    is_online: form.is_online,
    online_link: form.online_link,
    description: form.description,
    material_required: form.material_required,
    status: form.status,
    notes: form.notes,
    presenter_ids: form.presenters.map(p => p.id),
    presenter_durations: form.presenters.map(p => ({ id: p.id, duration: p.duration }))
  })
}

function close() {
  emit('close')
}
</script>