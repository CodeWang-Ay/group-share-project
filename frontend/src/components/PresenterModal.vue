<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-lg w-full mx-4 overflow-hidden">
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <div>
          <h2 class="text-lg font-bold text-gray-800">选择汇报人上传材料</h2>
          <p class="text-sm text-gray-500">{{ meetingTitle }}</p>
        </div>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>
      <div class="p-6">
        <div v-if="loading" class="text-sm text-gray-400">加载中...</div>
        <div v-else-if="presenters.length === 0" class="text-sm text-gray-400">该组会暂无汇报人，请先在组会安排中添加汇报人</div>
        <div v-else class="space-y-3">
          <div v-for="p in presenters" :key="p.id" class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                <i class="fa fa-user"></i>
              </div>
              <div>
                <p class="font-medium text-gray-800">{{ p.user?.real_name || p.user?.username || '未知' }}</p>
                <p class="text-xs text-gray-500">{{ p.duration_minutes }}分钟 · {{ p.presenter_type === 'assigned' ? '导师指定' : '主动报名' }}</p>
                <div class="mt-1">
                  <template v-if="p.files && p.files.length > 0">
                    <span v-for="f in p.files" :key="f.id" class="text-xs text-gray-500 mr-2"><i class="fa fa-file-o"></i>{{ f.filename }}</span>
                  </template>
                  <span v-else class="text-xs text-orange-500">未上传</span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span :class="confirmStatusClass(p.status)" class="text-xs px-2 py-1 rounded-full">{{ confirmStatusText(p.status) }}</span>
              <span :class="materialStatusClass(p)" class="text-xs px-2 py-1 rounded-full">{{ materialStatusText(p) }}</span>
              <button v-if="canConfirm(p)" @click="confirmAttendance(p.id)" class="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 transition-colors">
                <i class="fa fa-check"></i> 确认参会
              </button>
              <button v-if="isCurrentUser(p)" @click="$emit('upload', p.id, meetingId, p.user?.real_name || p.user?.username, meetingTitle)"
                      class="px-3 py-1 bg-primary text-white text-sm rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-1">
                <i class="fa fa-upload"></i> 上传
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="px-6 py-4 border-t flex justify-end">
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { materialApi } from '../api/material'

const props = defineProps({
  meetingId: Number,
  meetingTitle: String,
  userId: Number
})

defineEmits(['close', 'upload'])

const loading = ref(true)
const presenters = ref([])

function confirmStatusClass(status) {
  return status === 'confirmed' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-600'
}

function confirmStatusText(status) {
  return status === 'confirmed' ? '已确认参会' : '待确认参会'
}

function materialStatusClass(p) {
  const hasFiles = p.files && p.files.length > 0
  if (!hasFiles) return 'bg-orange-100 text-orange-600'
  if (p.material_status === 'pending') return 'bg-yellow-100 text-yellow-700'
  if (p.material_status === 'approved') return 'bg-green-100 text-green-700'
  return 'bg-red-100 text-red-700'
}

function materialStatusText(p) {
  const hasFiles = p.files && p.files.length > 0
  if (!hasFiles) return '待提交'
  if (p.material_status === 'pending') return '待审核'
  if (p.material_status === 'approved') return '已通过'
  return '已驳回'
}

function isCurrentUser(p) {
  return props.userId && p.user_id === props.userId
}

function canConfirm(p) {
  return isCurrentUser(p) && p.status === 'pending'
}

async function confirmAttendance(presenterId) {
  try {
    const res = await materialApi.confirmAttendance(presenterId)
    if (res.data.success) {
      window.$toast?.('已确认参会', 'success')
      loadPresenters()
    } else {
      window.$toast?.(res.data.message || '确认失败', 'error')
    }
  } catch (e) {
    console.error('确认参会失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function loadPresenters() {
  loading.value = true
  try {
    const res = await materialApi.getPresenters(props.meetingId)
    if (res.data.success) {
      presenters.value = res.data.data.presenters || []
    }
  } catch (e) {
    console.error('加载汇报人失败:', e)
  }
  loading.value = false
}

onMounted(() => {
  loadPresenters()
})
</script>