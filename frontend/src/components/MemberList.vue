<template>
  <div class="bg-white rounded-xl shadow-sm border overflow-hidden">
    <table class="w-full">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12">
            <input type="checkbox" :checked="allPageSelected" @change="handleSelectAll" class="w-4 h-4 text-blue-600 rounded border-gray-300">
          </th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户名</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">学号</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">手机号</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">学位</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">研究方向</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
          <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">加入时间</th>
          <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">操作</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr v-if="members.length === 0">
          <td colspan="10" class="px-4 py-8 text-center text-gray-500">暂无成员数据</td>
        </tr>
        <tr v-for="m in members" :key="m.id" class="hover:bg-gray-50 cursor-pointer" @click="toggleSelect(m.id)">
          <td class="px-4 py-3 w-12">
            <input type="checkbox" :checked="isSelected(m.id)" @change.stop="toggleSelect(m.id)" @click.stop class="w-4 h-4 text-blue-600 rounded border-gray-300">
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2 cursor-pointer" @click.stop="$emit('view', m)">
              <img :src="avatarUrl(m)" class="w-8 h-8 rounded-full object-cover hover:ring-2 hover:ring-blue-400">
              <span class="font-medium text-gray-800 hover:text-blue-600">{{ m.username }}</span>
            </div>
          </td>
          <td class="px-4 py-3 text-sm text-gray-600">{{ m.student_id || '未设置' }}</td>
          <td class="px-4 py-3 text-sm text-gray-600">{{ m.phone || '未设置' }}</td>
          <td class="px-4 py-3 text-sm text-gray-600">{{ m.degree_type || '未设置' }}</td>
          <td class="px-4 py-3 text-sm text-gray-600 truncate max-w-[100px]">{{ m.research_direction || '未设置' }}</td>
          <td class="px-4 py-3">
            <span :class="roleClass(m.role)">{{ roleText(m.role) }}</span>
          </td>
          <td class="px-4 py-3">
            <span :class="statusClass(m.status)">{{ statusText(m.status) }}</span>
          </td>
          <td class="px-4 py-3 text-sm text-gray-600">{{ formatDate(m.created_at) }}</td>
          <td class="px-4 py-3" @click.stop>
            <div class="flex items-center justify-center gap-1">
              <template v-if="isAdmin">
                <button @click="$emit('view', m)" class="p-1 text-green-600 hover:bg-green-50 rounded" title="查看详情"><i class="fa fa-eye"></i></button>
                <button @click="$emit('edit', m)" class="p-1 text-blue-600 hover:bg-blue-50 rounded" title="编辑"><i class="fa fa-edit"></i></button>
                <button @click="$emit('reset-password', m)" class="p-1 text-orange-600 hover:bg-orange-50 rounded" title="重置密码"><i class="fa fa-key"></i></button>
                <button @click="$emit('toggle-status', m)" class="p-1 rounded hover:bg-gray-50"
                        :class="m.status === 'active' ? 'text-gray-600' : 'text-green-600'" :title="m.status === 'active' ? '禁用' : '启用'">
                  <i :class="m.status === 'active' ? 'fa fa-ban' : 'fa fa-check-circle'"></i>
                </button>
                <button @click="$emit('delete', m)" class="p-1 text-red-600 hover:bg-red-50 rounded" title="删除"><i class="fa fa-trash"></i></button>
              </template>
              <template v-else>
                <button @click="$emit('view', m)" class="p-1 text-blue-600 hover:bg-blue-50 rounded" title="查看详情"><i class="fa fa-eye"></i></button>
                <button @click="$emit('send-message', m)" class="p-1 text-green-600 hover:bg-green-50 rounded" title="留言"><i class="fa fa-comment"></i></button>
              </template>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getAvatarUrl } from '../config'

const props = defineProps({
  members: Array,
  isAdmin: Boolean,
  selectedMembers: Array
})

const emit = defineEmits(['view', 'edit', 'delete', 'reset-password', 'toggle-status', 'send-message', 'toggle-select', 'select-all'])

const roleMap = { admin: '管理员', teacher: '导师', student: '学生' }
const statusMap = { active: '激活', inactive: '停用' }

function avatarUrl(m) {
  return getAvatarUrl(m.avatar, m.username)
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

function formatDate(dateStr) {
  if (!dateStr) return '未设置'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

function isSelected(id) {
  return props.selectedMembers?.includes(id)
}

function toggleSelect(id) {
  emit('toggle-select', id)
}

const allPageSelected = computed(() => {
  if (!props.members || props.members.length === 0) return false
  return props.members.every(m => isSelected(m.id))
})

function handleSelectAll() {
  emit('select-all', props.members.map(m => m.id))
}
</script>