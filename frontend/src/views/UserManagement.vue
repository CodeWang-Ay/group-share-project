<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <div class="mb-6">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">成员管理</h1>
          <p class="text-gray-500 mt-1">管理研究团队成员信息和权限</p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="showAddModal = true" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2">
            <i class="fa fa-plus"></i>
            <span>添加成员</span>
          </button>
          <button @click="exportMembers" class="bg-secondary text-white px-4 py-2 rounded-lg hover:bg-secondary/90 transition-colors flex items-center gap-2">
            <i class="fa fa-download"></i>
            <span>导出列表</span>
          </button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white rounded-xl p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-sm text-gray-600">总成员数</p><h3 class="text-2xl font-bold mt-1">{{ stats.total || 0 }}</h3></div>
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600"><i class="fa fa-users"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-sm text-gray-600">激活成员</p><h3 class="text-2xl font-bold mt-1 text-green-600">{{ stats.active || 0 }}</h3></div>
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-green-600"><i class="fa fa-check-circle"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-sm text-gray-600">导师数量</p><h3 class="text-2xl font-bold mt-1 text-purple-600">{{ stats.teacher || 0 }}</h3></div>
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600"><i class="fa fa-graduation-cap"></i></div>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 border">
          <div class="flex items-center justify-between">
            <div><p class="text-sm text-gray-600">研究生</p><h3 class="text-2xl font-bold mt-1 text-orange-600">{{ stats.student || 0 }}</h3></div>
            <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center text-orange-600"><i class="fa fa-graduation-cap"></i></div>
          </div>
        </div>
      </div>

      <!-- 筛选和搜索栏 -->
      <div class="bg-white rounded-xl border p-4 mb-6">
        <div class="flex flex-col lg:flex-row gap-4">
          <div class="flex-1">
            <div class="relative">
              <input v-model="searchKeyword" type="text" placeholder="搜索成员姓名、学号或邮箱..."
                     class="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
            </div>
          </div>
          <div class="flex flex-col sm:flex-row gap-3">
            <select v-model="roleFilter" class="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="">全部角色</option>
              <option value="admin">管理员</option>
              <option value="teacher">导师</option>
              <option value="student">学生</option>
            </select>
            <select v-model="statusFilter" class="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="">全部状态</option>
              <option value="active">激活</option>
              <option value="inactive">停用</option>
            </select>
            <select v-model="degreeFilter" class="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary/30 focus:border-primary">
              <option value="">全部学位</option>
              <option value="博士">博士</option>
              <option value="硕士">硕士</option>
              <option value="本科">本科</option>
              <option value="博士后">博士后</option>
            </select>
            <div class="bg-gray-100 rounded-lg p-1 flex">
              <button @click="viewMode = 'list'" :class="viewBtnClass('list')" title="列表视图">
                <i class="fa fa-list"></i>
              </button>
              <button @click="viewMode = 'grid'" :class="viewBtnClass('grid')" title="卡片视图">
                <i class="fa fa-th-large"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 批量操作工具栏 -->
      <div v-if="selectedMembers.length > 0" class="bg-blue-50 px-6 py-3 border-b border-blue-200 rounded-lg mb-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <span class="text-sm text-blue-700">已选择 {{ selectedMembers.length }} 个成员</span>
            <button @click="selectAll" class="text-sm text-blue-600 hover:text-blue-800">全选</button>
            <button @click="deselectAll" class="text-sm text-blue-600 hover:text-blue-800">取消全选</button>
          </div>
          <div class="flex items-center gap-2">
            <button @click="batchEditRole" class="px-3 py-1.5 text-sm bg-white text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50">
              <i class="fa fa-users mr-1"></i>批量修改角色
            </button>
            <button @click="batchEditStatus" class="px-3 py-1.5 text-sm bg-white text-green-600 border border-green-300 rounded-lg hover:bg-green-50">
              <i class="fa fa-power-off mr-1"></i>批量修改状态
            </button>
            <button @click="batchDelete" class="px-3 py-1.5 text-sm bg-white text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
              <i class="fa fa-trash mr-1"></i>批量删除
            </button>
            <button @click="deselectAll" class="px-3 py-1.5 text-sm bg-gray-200 text-gray-600 rounded-lg hover:bg-gray-300">取消</button>
          </div>
        </div>
      </div>

      <!-- 内容区域 -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        <i class="fa fa-spinner fa-spin mr-2"></i>加载中...
      </div>

      <!-- 列表视图 -->
      <MemberList v-else-if="viewMode === 'list'" :members="pageMembers" :is-admin="isAdmin"
                  @view="openViewModal" @edit="openEditModal" @delete="openDeleteModal"
                  @reset-password="openResetPasswordModal" @toggle-status="toggleMemberStatus"
                  @send-message="openSendMessageModal"
                  :selected-members="selectedMembers" @toggle-select="toggleSelect" @select-all="toggleSelectAll" />

      <!-- 卡片视图 -->
      <MemberGrid v-else :members="pageMembers" :is-admin="isAdmin"
                  @view="openViewModal" @edit="openEditModal" @delete="openDeleteModal"
                  @reset-password="openResetPasswordModal" @toggle-status="toggleMemberStatus" />

      <!-- 分页 -->
      <div v-if="filteredMembers.length > 0" class="mt-6 px-4 py-4 bg-white rounded-lg border flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600">每页显示</label>
            <select v-model="perPage" @change="currentPage = 1" class="px-3 py-1 border rounded-lg text-sm">
              <option :value="5">5条</option>
              <option :value="10">10条</option>
              <option :value="20">20条</option>
              <option :value="50">50条</option>
            </select>
          </div>
          <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ filteredMembers.length }} 条</div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="prevPage" :disabled="currentPage <= 1"
                  class="px-3 py-1 text-sm border rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <i class="fa fa-chevron-left mr-1"></i>上一页
          </button>
          <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
          <button @click="nextPage" :disabled="currentPage >= totalPages"
                  class="px-3 py-1 text-sm border rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            下一页<i class="fa fa-chevron-right ml-1"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 添加成员模态框 -->
    <AddMemberModal v-if="showAddModal" @close="showAddModal = false" @save="handleAddMember" />

    <!-- 编辑成员模态框 -->
    <EditMemberModal v-if="showEditModal" :member="editMember" :is-admin="isAdmin"
                     @close="closeEditModal" @save="handleUpdateMember" @reset-password="openResetPasswordModalFromEdit" />

    <!-- 查看成员详情模态框 -->
    <ViewMemberModal v-if="showViewModal" :member="viewMember" @close="closeViewModal" @edit="openEditModalFromView" @send-message="openSendMessageModalFromView" />

    <!-- 删除成员模态框 -->
    <DeleteMemberModal v-if="showDeleteModal" :member="deleteMember" @close="closeDeleteModal" @confirm="handleDeleteMember" />

    <!-- 重置密码模态框 -->
    <ResetPasswordModal v-if="showResetModal" :member="resetMember" @close="closeResetModal" @confirm="handleResetPassword" />

    <!-- 发送留言模态框 -->
    <SendMessageModal v-if="showMessageModal" :member="messageMember" @close="closeSendMessageModal" @send="handleSendMessage" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '../stores/user'
import { memberApi } from '../api/member'
import MemberList from '../components/MemberList.vue'
import MemberGrid from '../components/MemberGrid.vue'
import AddMemberModal from '../components/AddMemberModal.vue'
import EditMemberModal from '../components/EditMemberModal.vue'
import ViewMemberModal from '../components/ViewMemberModal.vue'
import DeleteMemberModal from '../components/DeleteMemberModal.vue'
import ResetPasswordModal from '../components/ResetPasswordModal.vue'
import SendMessageModal from '../components/SendMessageModal.vue'

const userStore = useUserStore()
const isAdmin = computed(() => userStore.role === 'admin')

const loading = ref(true)
const viewMode = ref('list')
const searchKeyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const degreeFilter = ref('')
const perPage = ref(10)
const currentPage = ref(1)

const allMembers = ref([])
const stats = ref({ total: 0, active: 0, teacher: 0, student: 0 })
const selectedMembers = ref([])

// 模态框状态
const showAddModal = ref(false)
const showEditModal = ref(false)
const showViewModal = ref(false)
const showDeleteModal = ref(false)
const showResetModal = ref(false)
const showMessageModal = ref(false)
const editMember = ref(null)
const viewMember = ref(null)
const deleteMember = ref(null)
const resetMember = ref(null)
const messageMember = ref(null)

let searchTimeout = null

// 计算属性
const filteredMembers = computed(() => {
  let members = allMembers.value

  if (roleFilter.value) {
    members = members.filter(m => m.role === roleFilter.value)
  }
  if (statusFilter.value) {
    members = members.filter(m => m.status === statusFilter.value)
  }
  if (degreeFilter.value) {
    members = members.filter(m => m.degree_type === degreeFilter.value)
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    members = members.filter(m => {
      const nameMatch = m.username && m.username.toLowerCase().includes(keyword)
      const idMatch = m.student_id && m.student_id.toLowerCase().includes(keyword)
      const emailMatch = m.email && m.email.toLowerCase().includes(keyword)
      return nameMatch || idMatch || emailMatch
    })
  }

  return members
})

const totalPages = computed(() => Math.ceil(filteredMembers.value.length / perPage.value) || 1)
const startItem = computed(() => (currentPage.value - 1) * perPage.value + 1)
const endItem = computed(() => Math.min(currentPage.value * perPage.value, filteredMembers.value.length))

const pageMembers = computed(() => {
  const start = (currentPage.value - 1) * perPage.value
  const end = start + perPage.value
  return filteredMembers.value.slice(start, end)
})

function viewBtnClass(mode) {
  return viewMode.value === mode
    ? 'px-3 py-2 rounded-md text-sm font-medium transition-all bg-white text-gray-900 shadow-sm'
    : 'px-3 py-2 rounded-md text-sm font-medium transition-all text-gray-500 hover:text-gray-700'
}

async function loadMembers() {
  loading.value = true
  try {
    const [membersRes, statsRes] = await Promise.all([
      memberApi.getMembers({ page: 1, per_page: 200 }),
      memberApi.getStats()
    ])

    if (membersRes.data.success) {
      allMembers.value = membersRes.data.data.members || []
    }
    if (statsRes.data.success) {
      stats.value = statsRes.data.data
    }
  } catch (e) {
    console.error('加载成员失败:', e)
  }
  loading.value = false
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value--
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++
}

function toggleSelect(memberId) {
  const idx = selectedMembers.value.indexOf(memberId)
  if (idx === -1) {
    selectedMembers.value.push(memberId)
  } else {
    selectedMembers.value.splice(idx, 1)
  }
}

function toggleSelectAll(pageMemberIds) {
  const allSelected = pageMemberIds.every(id => selectedMembers.value.includes(id))
  if (allSelected) {
    selectedMembers.value = selectedMembers.value.filter(id => !pageMemberIds.includes(id))
  } else {
    selectedMembers.value = [...new Set([...selectedMembers.value, ...pageMemberIds])]
  }
}

function selectAll() {
  selectedMembers.value = allMembers.value.map(m => m.id)
}

function deselectAll() {
  selectedMembers.value = []
}

function openViewModal(member) {
  viewMember.value = member
  showViewModal.value = true
}

function closeViewModal() {
  showViewModal.value = false
  viewMember.value = null
}

function openEditModal(member) {
  editMember.value = member
  showEditModal.value = true
  closeViewModal()
}

function openEditModalFromView(member) {
  openEditModal(member)
}

function closeEditModal() {
  showEditModal.value = false
  editMember.value = null
}

function openDeleteModal(member) {
  deleteMember.value = member
  showDeleteModal.value = true
}

function closeDeleteModal() {
  showDeleteModal.value = false
  deleteMember.value = null
}

function openResetPasswordModal(member) {
  resetMember.value = member
  showResetModal.value = true
}

function openResetPasswordModalFromEdit(member) {
  resetMember.value = member
  showResetModal.value = true
}

function closeResetModal() {
  showResetModal.value = false
  resetMember.value = null
}

function openSendMessageModal(member) {
  messageMember.value = member
  showMessageModal.value = true
}

function openSendMessageModalFromView(member) {
  messageMember.value = member
  showMessageModal.value = true
  closeViewModal()
}

function closeSendMessageModal() {
  showMessageModal.value = false
  messageMember.value = null
}

async function handleAddMember(data) {
  try {
    const res = await memberApi.addMember(data)
    if (res.data.success) {
      window.$toast?.('成员添加成功', 'success')
      showAddModal.value = false
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '添加失败', 'error')
    }
  } catch (e) {
    console.error('添加成员失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function handleUpdateMember(data) {
  try {
    const res = await memberApi.updateMember(editMember.value.id, data)
    if (res.data.success) {
      window.$toast?.('成员信息更新成功', 'success')
      closeEditModal()
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '更新失败', 'error')
    }
  } catch (e) {
    console.error('更新成员失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function handleDeleteMember() {
  try {
    const res = await memberApi.deleteMember(deleteMember.value.id)
    if (res.data.success) {
      window.$toast?.('成员删除成功', 'success')
      closeDeleteModal()
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '删除失败', 'error')
    }
  } catch (e) {
    console.error('删除成员失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function handleResetPassword() {
  try {
    const res = await memberApi.resetPassword(resetMember.value.id, '123456')
    if (res.data.success) {
      window.$toast?.('密码重置成功，新密码: 123456', 'success')
      closeResetModal()
    } else {
      window.$toast?.(res.data.message || '重置失败', 'error')
    }
  } catch (e) {
    console.error('重置密码失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function toggleMemberStatus(member) {
  const newStatus = member.status === 'active' ? 'inactive' : 'active'
  try {
    const res = await memberApi.updateStatus(member.id, newStatus)
    if (res.data.success) {
      window.$toast?.(`成员${newStatus === 'active' ? '启用' : '禁用'}成功`, 'success')
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '操作失败', 'error')
    }
  } catch (e) {
    console.error('状态更新失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function handleSendMessage(data) {
  try {
    const res = await memberApi.sendMessage(messageMember.value.id, data.title, data.content)
    if (res.data.success) {
      window.$toast?.('留言发送成功', 'success')
      closeSendMessageModal()
    } else {
      window.$toast?.(res.data.message || '发送失败', 'error')
    }
  } catch (e) {
    console.error('发送留言失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function batchEditRole() {
  if (selectedMembers.value.length === 0) return
  const role = prompt('请输入新角色（admin/teacher/student）：')
  if (!role || !['admin', 'teacher', 'student'].includes(role)) {
    window.$toast?.('角色必须是 admin、teacher 或 student', 'error')
    return
  }
  try {
    const res = await memberApi.batchUpdateRole(selectedMembers.value, role)
    if (res.data.success || res.status === 200) {
      window.$toast?.(`成功更新 ${res.data.updated_count || selectedMembers.value.length} 个成员的角色`, 'success')
      deselectAll()
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '操作失败', 'error')
    }
  } catch (e) {
    console.error('批量更新角色失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function batchEditStatus() {
  if (selectedMembers.value.length === 0) return
  const status = prompt('请输入新状态（active/inactive）：')
  if (!status || !['active', 'inactive'].includes(status)) {
    window.$toast?.('状态必须是 active 或 inactive', 'error')
    return
  }
  try {
    const res = await memberApi.batchUpdateStatus(selectedMembers.value, status)
    if (res.data.success || res.status === 200) {
      window.$toast?.(`成功更新 ${res.data.updated_count || selectedMembers.value.length} 个成员的状态`, 'success')
      deselectAll()
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '操作失败', 'error')
    }
  } catch (e) {
    console.error('批量更新状态失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

async function batchDelete() {
  if (selectedMembers.value.length === 0) return
  if (!confirm(`确定要删除选中的 ${selectedMembers.value.length} 个成员吗？此操作不可撤销！`)) return
  try {
    const res = await memberApi.batchDelete(selectedMembers.value)
    if (res.data.success || res.status === 200) {
      window.$toast?.(`成功删除 ${res.data.deleted_count || selectedMembers.value.length} 个成员`, 'success')
      deselectAll()
      loadMembers()
    } else {
      window.$toast?.(res.data.message || '操作失败', 'error')
    }
  } catch (e) {
    console.error('批量删除失败:', e)
    window.$toast?.('网络错误', 'error')
  }
}

function exportMembers() {
  window.$toast?.('成员列表导出成功', 'success')
}

onMounted(() => {
  loadMembers()
})

watch([roleFilter, statusFilter, degreeFilter], () => { currentPage.value = 1 })
watch(searchKeyword, () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => { currentPage.value = 1 }, 300)
})
</script>