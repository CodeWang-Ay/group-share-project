<template>
  <div class="p-6">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">研究任务管理</h1>
      <p class="text-gray-500">跟踪和管理研究任务的进度</p>
    </div>

    <!-- 状态筛选和搜索 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <!-- 状态筛选按钮 -->
        <div class="flex flex-wrap gap-2">
          <button @click="filterByStatus('')" :class="statusBtnClass('')" class="task-status-btn">全部任务</button>
          <button @click="filterByStatus('pending')" :class="statusBtnClass('pending')" class="task-status-btn">待开始</button>
          <button @click="filterByStatus('ongoing')" :class="statusBtnClass('ongoing')" class="task-status-btn">进行中</button>
          <button @click="filterByStatus('completed')" :class="statusBtnClass('completed')" class="task-status-btn">已完成</button>
          <button @click="filterByStatus('overdue')" :class="statusBtnClass('overdue')" class="task-status-btn">已逾期</button>
        </div>

        <!-- 搜索和操作 -->
        <div class="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <div class="relative flex-1 sm:flex-initial">
            <input v-model="searchKeyword" type="text" @input="onSearchInput"
                   class="w-full sm:w-64 px-4 py-2 pl-10 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary"
                   placeholder="搜索任务...">
            <i class="fa fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"></i>
          </div>

          <!-- 布局切换 -->
          <div class="flex items-center gap-2 border border-gray-200 rounded-lg p-1">
            <button @click="setLayout('list')" :class="layoutBtnClass('list')" class="p-2 rounded transition-colors" title="列表视图">
              <i class="fa fa-list"></i>
            </button>
            <button @click="setLayout('grid')" :class="layoutBtnClass('grid')" class="p-2 rounded transition-colors" title="卡片视图">
              <i class="fa fa-th-large"></i>
            </button>
          </div>

          <!-- 新建任务 -->
          <button @click="openCreateModal" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 flex items-center gap-2">
            <i class="fa fa-plus"></i><span>新建任务</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div><p class="text-gray-500 text-sm">总任务数</p><h3 class="text-2xl font-bold mt-1">{{ stats.total || 0 }}</h3></div>
          <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-primary"><i class="fa fa-tasks"></i></div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div><p class="text-gray-500 text-sm">待开始</p><h3 class="text-2xl font-bold mt-1">{{ stats.pending_count || 0 }}</h3></div>
          <div class="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600"><i class="fa fa-clock-o"></i></div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div><p class="text-gray-500 text-sm">进行中</p><h3 class="text-2xl font-bold mt-1">{{ stats.ongoing_count || 0 }}</h3></div>
          <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600"><i class="fa fa-spinner"></i></div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div><p class="text-gray-500 text-sm">已完成</p><h3 class="text-2xl font-bold mt-1">{{ stats.completed_count || 0 }}</h3></div>
          <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600"><i class="fa fa-check-circle"></i></div>
        </div>
      </div>
      <div class="bg-white rounded-lg p-4 border border-gray-100">
        <div class="flex items-center justify-between">
          <div><p class="text-gray-500 text-sm">逾期任务</p><h3 class="text-2xl font-bold mt-1">{{ stats.overdue_count || 0 }}</h3></div>
          <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600"><i class="fa fa-exclamation-triangle"></i></div>
        </div>
      </div>
    </div>

    <!-- 网格视图 -->
    <div v-show="currentLayout === 'grid'">
      <div v-if="tasks.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div v-for="task in tasks" :key="task.id"
             class="bg-white rounded-xl shadow-sm p-5 task-card-hover border border-gray-100">
          <div class="flex justify-between items-start mb-3">
            <span :class="priorityClass(task.priority)" class="task-priority">{{ task.priority_text }}</span>
            <span :class="statusClass(task.display_status)" class="task-status-btn">{{ task.status_text }}</span>
          </div>
          <h4 class="font-semibold text-gray-800 mb-2">{{ task.title }}</h4>
          <p class="text-sm text-gray-500 mb-3 line-clamp-2">{{ task.description || '无描述' }}</p>
          <div class="mb-3">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>进度</span>
              <span>{{ task.progress }}%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div class="bg-primary h-2 rounded-full transition-all" :style="{ width: task.progress + '%' }"></div>
            </div>
          </div>
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">
                <i class="fa fa-user"></i>
              </div>
              <span>{{ task.assignee?.username || '未知' }}</span>
            </div>
            <span class="text-gray-400"><i class="fa fa-calendar"></i> {{ formatDeadline(task.deadline) }}</span>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-100 flex justify-end gap-3">
            <button @click="viewTask(task.id)" class="text-gray-400 hover:text-primary transition-colors" title="详情"><i class="fa fa-eye"></i></button>
            <button @click="openEditModal(task.id)" class="text-gray-400 hover:text-yellow-500 transition-colors" title="编辑"><i class="fa fa-pencil"></i></button>
            <button @click="openDeleteModal(task.id, task.title)" class="text-gray-400 hover:text-red-500 transition-colors" title="删除"><i class="fa fa-trash-o"></i></button>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-12 text-gray-500">
        <i class="fa fa-tasks text-4xl mb-3"></i><p>暂无任务</p>
      </div>

      <!-- 网格视图分页 -->
      <div v-if="totalCount > 0" class="mt-6 px-4 py-3 bg-white rounded-lg border border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-600">每页显示</label>
              <select v-model="perPage" @change="changePerPage" class="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="5">5条</option>
                <option value="10">10条</option>
                <option value="20">20条</option>
              </select>
            </div>
            <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ totalCount }} 条</div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="prevPage" :disabled="currentPage <= 1"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              <i class="fa fa-chevron-left mr-1"></i>上一页
            </button>
            <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
            <button @click="nextPage" :disabled="currentPage >= totalPages"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              下一页<i class="fa fa-chevron-right ml-1"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-show="currentLayout === 'list'" class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <!-- 表格头部 -->
      <div class="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div class="grid grid-cols-12 gap-4 items-center text-xs font-medium text-gray-500 uppercase tracking-wider">
          <div class="col-span-4">任务标题</div>
          <div class="col-span-1 text-center">优先级</div>
          <div class="col-span-1 text-center">进度</div>
          <div class="col-span-2 text-center">状态</div>
          <div class="col-span-2 text-center">负责人</div>
          <div class="col-span-2 text-center">操作</div>
        </div>
      </div>

      <!-- 表格内容 -->
      <div class="divide-y divide-gray-100">
        <div v-if="tasks.length > 0">
          <div v-for="task in tasks" :key="task.id" class="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div class="grid grid-cols-12 gap-4 items-center">
              <div class="col-span-4">
                <div class="flex items-center gap-3">
                  <div>
                    <h4 class="font-medium text-gray-800">{{ task.title }}</h4>
                    <p class="text-xs text-gray-500 line-clamp-1">{{ task.description || '无描述' }}</p>
                  </div>
                </div>
              </div>
              <div class="col-span-1 text-center">
                <span :class="priorityClass(task.priority)" class="task-priority">{{ task.priority_text }}</span>
              </div>
              <div class="col-span-1 text-center text-sm text-gray-600">{{ task.progress }}%</div>
              <div class="col-span-2 text-center">
                <span :class="statusClass(task.display_status)" class="task-status-btn">{{ task.status_text }}</span>
              </div>
              <div class="col-span-2 text-center">
                <div class="flex items-center justify-center gap-2">
                  <div class="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs">
                    <i class="fa fa-user"></i>
                  </div>
                  <span class="text-sm">{{ task.assignee?.username || '未知' }}</span>
                </div>
              </div>
              <div class="col-span-2 text-center">
                <div class="flex items-center justify-center gap-2">
                  <button @click="viewTask(task.id)" class="text-gray-400 hover:text-primary transition-colors p-1" title="详情"><i class="fa fa-eye"></i></button>
                  <button @click="openEditModal(task.id)" class="text-gray-400 hover:text-yellow-500 transition-colors p-1" title="编辑"><i class="fa fa-pencil"></i></button>
                  <button @click="openDeleteModal(task.id, task.title)" class="text-gray-400 hover:text-red-500 transition-colors p-1" title="删除"><i class="fa fa-trash-o"></i></button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-12 text-gray-500"><p>暂无任务</p></div>
      </div>

      <!-- 列表视图分页 -->
      <div v-if="totalCount > 0" class="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <label class="text-sm text-gray-600">每页显示</label>
              <select v-model="perPage" @change="changePerPage" class="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/30 focus:border-primary">
                <option value="5">5条</option>
                <option value="10">10条</option>
                <option value="20">20条</option>
              </select>
            </div>
            <div class="text-sm text-gray-600">显示第 {{ startItem }}-{{ endItem }} 条，共 {{ totalCount }} 条</div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="prevPage" :disabled="currentPage <= 1"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              <i class="fa fa-chevron-left mr-1"></i>上一页
            </button>
            <span class="px-3 py-1 text-sm text-gray-600">第 {{ currentPage }} 页</span>
            <button @click="nextPage" :disabled="currentPage >= totalPages"
                    class="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              下一页<i class="fa fa-chevron-right ml-1"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务详情模态框 -->
    <TaskDetailModal
      v-model="detailModalVisible"
      :task="currentTask"
      @close="detailModalVisible = false"
      @edit="openEditModalFromDetail"
    />

    <!-- 新建任务模态框 -->
    <CreateTaskModal
      v-model="createModalVisible"
      :user-role="userStore.role"
      :members="membersList"
      @submit="submitCreateTask"
      @close="createModalVisible = false"
    />

    <!-- 编辑任务模态框 -->
    <EditTaskModal
      v-model="editModalVisible"
      :task="currentTask"
      @submit="submitEditTask"
      @close="editModalVisible = false"
    />

    <!-- 删除确认模态框 -->
    <DeleteTaskModal
      v-model="deleteModalVisible"
      :task-id="deleteTaskId"
      :task-title="deleteTaskTitle"
      @confirm="confirmDelete"
      @close="deleteModalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { taskApi } from '../api/research_tasks'
import { memberApi } from '../api/member'
import TaskDetailModal from '../components/TaskDetailModal.vue'
import CreateTaskModal from '../components/CreateTaskModal.vue'
import EditTaskModal from '../components/EditTaskModal.vue'
import DeleteTaskModal from '../components/DeleteTaskModal.vue'

const userStore = useUserStore()

// 任务数据
const tasks = ref([])
const stats = ref({
  total: 0,
  pending_count: 0,
  ongoing_count: 0,
  completed_count: 0,
  overdue_count: 0
})

// 分页
const currentPage = ref(1)
const perPage = ref(5)
const totalCount = ref(0)
const totalPages = ref(1)

// 筛选
const currentStatus = ref('')
const searchKeyword = ref('')
const sortBy = ref('deadline')
const sortOrder = ref('asc')

// 布局
const currentLayout = ref(localStorage.getItem('task_layout') || 'list')

// 模态框
const detailModalVisible = ref(false)
const createModalVisible = ref(false)
const editModalVisible = ref(false)
const deleteModalVisible = ref(false)
const currentTask = ref(null)
const deleteTaskId = ref(null)
const deleteTaskTitle = ref('')

// 成员列表
const membersList = ref([])

// 计算属性
const startItem = computed(() => (currentPage.value - 1) * perPage.value + 1)
const endItem = computed(() => Math.min(currentPage.value * perPage.value, totalCount.value))

// 搜索延迟
let searchTimeout = null
const onSearchInput = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadTasks()
  }, 300)
}

// 加载任务统计
const loadStats = async () => {
  try {
    const res = await taskApi.getStats()
    if (res.data.success) {
      stats.value = res.data.data
    }
  } catch (e) {
    console.error('加载任务统计失败:', e)
  }
}

// 加载任务列表
const loadTasks = async () => {
  try {
    const params = {
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    if (currentStatus.value) params.status = currentStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value

    const res = await taskApi.getTasks(params)
    if (res.data.success) {
      tasks.value = res.data.data.tasks
      const pagination = res.data.data.pagination
      totalCount.value = pagination.total || 0
      totalPages.value = pagination.total_pages || 1
    }
  } catch (e) {
    console.error('加载任务列表失败:', e)
  }
}

// 加载成员列表
const loadMembers = async () => {
  if (userStore.role === 'teacher' || userStore.role === 'admin') {
    try {
      const res = await memberApi.getMembers()
      if (res.data.success) {
        membersList.value = res.data.data.members || []
      }
    } catch (e) {
      console.error('加载成员列表失败:', e)
    }
  }
}

// 状态筛选
const filterByStatus = (status) => {
  currentStatus.value = status
  currentPage.value = 1
  loadTasks()
}

// 布局切换
const setLayout = (layout) => {
  currentLayout.value = layout
  localStorage.setItem('task_layout', layout)
}

// 分页操作
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    loadTasks()
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadTasks()
  }
}

const changePerPage = () => {
  currentPage.value = 1
  loadTasks()
}

// 样式类
const statusBtnClass = (status) => {
  return currentStatus.value === status ? 'bg-primary text-white active' : ''
}

const layoutBtnClass = (layout) => {
  return currentLayout.value === layout ? 'bg-primary text-white' : 'text-gray-500'
}

const priorityClass = (priority) => {
  if (priority === 'high') return 'priority-high'
  if (priority === 'low') return 'priority-low'
  return 'priority-middle'
}

const statusClass = (displayStatus) => {
  if (displayStatus === 'overdue') return 'status-overdue'
  if (displayStatus === 'ongoing') return 'status-doing'
  if (displayStatus === 'completed') return 'status-finish'
  return 'status-wait'
}

const formatDeadline = (deadline) => {
  if (!deadline) return '无截止日期'
  return new Date(deadline).toLocaleDateString('zh-CN')
}

// 模态框操作
const viewTask = async (id) => {
  try {
    const res = await taskApi.getTaskDetail(id)
    if (res.data.success) {
      currentTask.value = res.data.data
      detailModalVisible.value = true
    }
  } catch (e) {
    console.error('获取任务详情失败:', e)
  }
}

const openCreateModal = () => {
  loadMembers()
  createModalVisible.value = true
}

const openEditModal = async (id) => {
  try {
    const res = await taskApi.getTaskDetail(id)
    if (res.data.success) {
      currentTask.value = res.data.data
      editModalVisible.value = true
    }
  } catch (e) {
    console.error('获取任务详情失败:', e)
  }
}

const openEditModalFromDetail = () => {
  detailModalVisible.value = false
  editModalVisible.value = true
}

const openDeleteModal = (id, title) => {
  deleteTaskId.value = id
  deleteTaskTitle.value = title
  deleteModalVisible.value = true
}

// 提交创建任务
const submitCreateTask = async (formData) => {
  try {
    const res = await taskApi.createTask(formData)
    if (res.data.success) {
      createModalVisible.value = false
      loadStats()
      loadTasks()
    } else {
      alert(res.data.message || '创建失败')
    }
  } catch (e) {
    console.error('创建任务失败:', e)
    alert('网络错误，请重试')
  }
}

// 提交编辑任务
const submitEditTask = async (formData) => {
  try {
    const res = await taskApi.updateTask(currentTask.value.id, formData)
    if (res.data.success) {
      editModalVisible.value = false
      detailModalVisible.value = false
      loadStats()
      loadTasks()
    } else {
      alert(res.data.message || '更新失败')
    }
  } catch (e) {
    console.error('更新任务失败:', e)
    alert('网络错误，请重试')
  }
}

// 确认删除
const confirmDelete = async () => {
  try {
    const res = await taskApi.deleteTask(deleteTaskId.value)
    if (res.data.success) {
      deleteModalVisible.value = false
      loadStats()
      loadTasks()
    } else {
      alert(res.data.message || '删除失败')
    }
  } catch (e) {
    console.error('删除任务失败:', e)
    alert('网络错误，请重试')
  }
}

// 初始化
onMounted(() => {
  loadStats()
  loadTasks()
})
</script>

<style scoped>
.task-card-hover {
  transition: all 0.2s;
}
.task-card-hover:hover {
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  transform: translateY(-2px);
}
.task-priority {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-weight: 500;
}
.priority-high {
  background-color: #fee2e2;
  color: #dc2626;
}
.priority-middle {
  background-color: #fef3c7;
  color: #d97706;
}
.priority-low {
  background-color: #d1fae5;
  color: #059669;
}
.task-status-btn {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  cursor: pointer;
  transition: all;
}
.task-status-btn:hover {
  background-color: #2563eb;
  color: white;
}
.task-status-btn.active {
  background-color: #2563eb;
  color: white;
}
.status-wait {
  background-color: #f3f4f6;
  color: #4b5563;
}
.status-doing {
  background-color: #dbeafe;
  color: #2563eb;
}
.status-finish {
  background-color: #d1fae5;
  color: #059669;
}
.status-overdue {
  background-color: #fee2e2;
  color: #dc2626;
}
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>