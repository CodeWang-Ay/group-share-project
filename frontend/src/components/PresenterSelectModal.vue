<template>
  <div v-if="visible" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-md w-full mx-4 overflow-hidden">
      <!-- 头部 -->
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <div>
          <h2 class="text-lg font-bold text-gray-800">选择汇报人</h2>
          <p class="text-sm text-gray-500">已选择 {{ selectedMembers.length }} 人</p>
        </div>
        <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
          <i class="fa fa-times text-xl"></i>
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="px-6 py-4 border-b">
        <div class="relative">
          <input v-model="searchKeyword" type="text"
                 class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary"
                 placeholder="搜索成员姓名...">
          <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
        </div>
      </div>

      <!-- 成员列表 -->
      <div class="p-6 max-h-60 overflow-y-auto">
        <div v-if="loading" class="text-center text-sm text-gray-400">
          <i class="fa fa-spinner fa-spin mr-2"></i>加载中...
        </div>
        <div v-else-if="filteredMembers.length === 0" class="text-center text-sm text-gray-400">
          <i class="fa fa-user-times text-2xl mb-2"></i>
          <p>未找到匹配的成员</p>
        </div>
        <div v-else class="space-y-2">
          <div v-for="m in filteredMembers" :key="m.id"
               @click="toggleSelect(m)"
               :class="isSelected(m.id) ? 'bg-primary/10 border-primary' : 'bg-gray-50 border-gray-100 hover:bg-gray-100'"
               class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors">
            <img :src="getAvatarUrl(m.avatar, m.username)" class="w-10 h-10 rounded-full object-cover">
            <div class="flex-1">
              <p class="font-medium text-gray-800">{{ m.real_name || m.username }}</p>
              <p class="text-xs text-gray-500">{{ m.degree_type || (m.role === 'teacher' ? '导师' : m.role === 'admin' ? '管理员' : '学生') }}</p>
            </div>
            <div v-if="isSelected(m.id)" class="w-6 h-6 rounded-full bg-primary text-white flex items-center justify-center">
              <i class="fa fa-check text-xs"></i>
            </div>
          </div>
        </div>
      </div>

      <!-- 已选择的汇报人 -->
      <div v-if="selectedMembers.length > 0" class="px-6 py-3 bg-gray-50 border-t">
        <p class="text-sm text-gray-500 mb-2">已选择的汇报人：</p>
        <div class="flex flex-wrap gap-2">
          <span v-for="m in selectedMembers" :key="m.id"
                class="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded-full text-sm">
            {{ m.real_name || m.username }}
            <button @click="toggleSelect(m)" class="hover:text-red-500">
              <i class="fa fa-times text-xs"></i>
            </button>
          </span>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="px-6 py-4 border-t flex justify-end gap-3">
        <button @click="close" class="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
          取消
        </button>
        <button @click="confirmSelect" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
          确认选择
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { meetingApi } from '../api/meeting'
import { getAvatarUrl } from '../config'

const props = defineProps({
  selectedIds: Array
})
const emit = defineEmits(['select'])

const visible = defineModel()
const searchKeyword = ref('')
const loading = ref(false)
const allMembers = ref([])
const selectedIds = ref([...(props.selectedIds || [])])

const filteredMembers = computed(() => {
  if (!searchKeyword.value) return allMembers.value
  const keyword = searchKeyword.value.toLowerCase()
  return allMembers.value.filter(m =>
    (m.username?.toLowerCase().includes(keyword)) ||
    (m.real_name?.toLowerCase().includes(keyword))
  )
})

const selectedMembers = computed(() => {
  return allMembers.value.filter(m => selectedIds.value.includes(m.id))
})

function isSelected(id) {
  return selectedIds.value.includes(id)
}

function toggleSelect(m) {
  const idx = selectedIds.value.indexOf(m.id)
  if (idx === -1) {
    selectedIds.value.push(m.id)
  } else {
    selectedIds.value.splice(idx, 1)
  }
}

async function loadMembers() {
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

function confirmSelect() {
  emit('select', selectedMembers.value)
  visible.value = false
}

function close() {
  visible.value = false
}

onMounted(() => {
  loadMembers()
})
</script>