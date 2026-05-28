<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
    <template v-if="members.length === 0">
      <div class="text-center py-12 text-gray-500 col-span-full">
        <p><i class="fa fa-folder-open-o text-4xl mb-4 block"></i>暂无成员数据</p>
      </div>
    </template>
    <template v-else>
      <div v-for="m in members" :key="m.id" class="bg-white rounded-xl shadow-sm border p-4 flex flex-col min-h-[200px]">
        <div class="flex items-center gap-3 mb-3 cursor-pointer" @click="$emit('view', m)">
          <img :src="avatarUrl(m)" class="w-12 h-12 rounded-full object-cover hover:ring-2 hover:ring-blue-400">
          <div class="flex-1">
            <p class="font-medium text-gray-800 hover:text-blue-600">{{ m.username }}</p>
            <p class="text-sm text-gray-500">{{ m.student_id || '未设置' }}</p>
          </div>
        </div>
        <div class="space-y-2 flex-1">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">角色</span>
            <span :class="roleClass(m.role)">{{ roleText(m.role) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">状态</span>
            <span :class="statusClass(m.status)">{{ statusText(m.status) }}</span>
          </div>
          <div class="text-sm text-gray-600">
            <p class="truncate">{{ m.email || '未设置邮箱' }}</p>
            <p class="text-xs truncate">{{ m.research_direction || '未设置研究方向' }}</p>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4 flex-wrap">
          <button @click="$emit('edit', m)" class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded">
            <i class="fa fa-edit mr-1"></i>编辑
          </button>
          <template v-if="isAdmin">
            <button @click="$emit('reset-password', m)" class="px-3 py-1 text-sm text-orange-600 hover:bg-orange-50 rounded">
              <i class="fa fa-key mr-1"></i>重置
            </button>
            <button @click="$emit('toggle-status', m)" class="px-3 py-1 text-sm rounded"
                    :class="m.status === 'active' ? 'text-gray-600 hover:bg-gray-50' : 'text-green-600 hover:bg-green-50'">
              <i :class="m.status === 'active' ? 'fa fa-ban mr-1' : 'fa fa-check-circle mr-1'"></i>{{ m.status === 'active' ? '禁用' : '启用' }}
            </button>
            <button @click="$emit('delete', m)" class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded">
              <i class="fa fa-trash mr-1"></i>删除
            </button>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  members: Array,
  isAdmin: Boolean
})

defineEmits(['view', 'edit', 'delete', 'reset-password', 'toggle-status'])

const roleMap = { admin: '管理员', teacher: '导师', student: '学生' }
const statusMap = { active: '激活', inactive: '停用' }

function avatarUrl(m) {
  if (m.avatar) {
    if (m.avatar.startsWith('/uploads')) return `http://localhost:8081${m.avatar}`
    return m.avatar
  }
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(m.username || 'User')}&background=random&size=128`
}

function roleText(role) { return roleMap[role] || role }
function statusText(status) { return statusMap[status] || status }

function roleClass(role) {
  const classes = {
    admin: 'inline-flex px-2 py-1 text-xs font-medium rounded-full text-purple-600 bg-purple-100',
    teacher: 'inline-flex px-2 py-1 text-xs font-medium rounded-full text-blue-600 bg-blue-100',
    student: 'inline-flex px-2 py-1 text-xs font-medium rounded-full text-orange-600 bg-orange-100'
  }
  return classes[role] || classes.student
}

function statusClass(status) {
  return status === 'active'
    ? 'inline-flex px-2 py-1 text-xs font-medium rounded-full text-green-600 bg-green-100'
    : 'inline-flex px-2 py-1 text-xs font-medium rounded-full text-red-600 bg-red-100'
}
</script>
}