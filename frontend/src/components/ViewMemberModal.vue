<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col overflow-hidden">
      <div class="p-4 border-b flex-shrink-0 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-800">成员详情</h3>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600"><i class="fa fa-times text-xl"></i></button>
      </div>
      <div class="p-6 flex-1 overflow-y-auto">
        <div class="flex items-center gap-4 mb-6">
          <img :src="avatarUrl" class="w-16 h-16 rounded-full object-cover border-2 border-gray-200">
          <div>
            <h4 class="text-xl font-semibold text-gray-800">{{ member?.username }}</h4>
            <p class="text-sm text-gray-500">{{ roleText }} · {{ statusText }}</p>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <div>
              <label class="text-sm text-gray-500">学号/工号</label>
              <p class="text-base font-medium text-gray-800">{{ member?.student_id || '未设置' }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">手机号</label>
              <p class="text-base font-medium text-gray-800">{{ member?.phone || '未设置' }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">邮箱</label>
              <p class="text-base font-medium text-gray-800">{{ member?.email || '未设置' }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">学位类型</label>
              <p class="text-base font-medium text-gray-800">{{ member?.degree_type || '未设置' }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">性别</label>
              <p class="text-base font-medium text-gray-800">{{ genderText }}</p>
            </div>
          </div>
          <div class="space-y-4">
            <div>
              <label class="text-sm text-gray-500">研究方向</label>
              <p class="text-base font-medium text-gray-800">{{ member?.research_direction || '未设置' }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">状态</label>
              <p class="text-base font-medium text-gray-800">{{ statusText }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">加入时间</label>
              <p class="text-base font-medium text-gray-800">{{ formatDate(member?.created_at) }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">身份证号码</label>
              <p class="text-base font-medium text-gray-800">{{ member?.id_card || '未设置' }}</p>
            </div>
            <div>
              <label class="text-sm text-gray-500">银行卡号</label>
              <p class="text-base font-medium text-gray-800">{{ member?.bank_card || '未设置' }}</p>
            </div>
          </div>
        </div>
      </div>
      <div class="p-4 border-t flex justify-end gap-3 flex-shrink-0 bg-white">
        <button @click="$emit('send-message', member)" class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 flex items-center gap-2">
          <i class="fa fa-comment"></i>留言
        </button>
        <button @click="$emit('edit', member)" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center gap-2">
          <i class="fa fa-edit"></i>编辑
        </button>
        <button @click="$emit('close')" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  member: Object
})

const emit = defineEmits(['close', 'edit', 'send-message'])

const roleMap = { admin: '管理员', teacher: '导师', student: '学生' }
const statusMap = { active: '激活', inactive: '停用' }
const genderMap = { male: '男', female: '女' }

const roleText = computed(() => roleMap[props.member?.role] || '未设置')
const statusText = computed(() => statusMap[props.member?.status] || '未设置')
const genderText = computed(() => genderMap[props.member?.gender] || '未设置')

const avatarUrl = computed(() => {
  if (props.member?.avatar) {
    if (props.member.avatar.startsWith('/uploads')) return `http://localhost:8081${props.member.avatar}`
    return props.member.avatar
  }
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(props.member?.username || 'User')}&background=random&size=128`
})

function formatDate(dateStr) {
  if (!dateStr) return '未设置'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}
</script>
}