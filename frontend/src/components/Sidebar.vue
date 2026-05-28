<template>
  <aside :class="sidebarClass">
    <div v-if="isMobile" class="sticky top-0 bg-white border-b p-4 z-10">
      <div class="flex justify-between items-center">
        <span class="font-semibold">菜单</span>
        <button @click="close" class="p-2 rounded-lg hover:bg-gray-100">
          <i class="fa fa-times text-gray-600"></i>
        </button>
      </div>
    </div>

    <div class="p-4 overflow-y-auto h-full">
      <!-- 用户信息 -->
      <div class="bg-gradient-to-r from-primary/5 to-primary/10 rounded-xl p-4 mb-6">
        <div class="flex items-center gap-3">
          <img :src="avatarUrl"
               class="w-12 h-12 rounded-full border-2 border-white shadow-sm object-cover">
          <div>
            <p class="font-semibold text-gray-800">{{ userStore.username }}</p>
            <span class="text-sm bg-primary text-white px-2 py-0.5 rounded-full">
              {{ userStore.roleText }}
            </span>
          </div>
        </div>
      </div>

      <nav>
        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3">组会管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-dashboard" text="工作台" to="/" />
          <MenuItem icon="fa-calendar" text="组会安排" to="/meeting-schedule" />
          <MenuItem icon="fa-file-text-o" text="汇报材料" to="/report-materials" />
          <MenuItem icon="fa-comments-o" text="组会记录" to="/meeting-record" />
        </ul>

        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3 mt-6">资源管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-book" text="学术文献" href="/rm_paper_database" />
          <MenuItem icon="fa-folder-open-o" text="共享资料" href="/rm_share_file" />
          <MenuItem icon="fa-tasks" text="研究任务" href="/rm_research_tasks" />
        </ul>

        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3 mt-6">团队管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-users" text="成员管理" to="/user-management" />
          <MenuItem icon="fa-graduation-cap" text="学术工具" to="/academic-tools" />
          <MenuItem icon="fa-line-chart" text="研究进展" href="/tm_research_progress" />
        </ul>
      </nav>
    </div>
  </aside>

  <div v-if="visible && isMobile" @click="close" class="fixed inset-0 bg-black/50 z-30 lg:hidden"></div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'
import MenuItem from './MenuItem.vue'

const userStore = useUserStore()
const visible = defineModel()

const isMobile = ref(window.innerWidth < 1024)

// 头像URL处理
const avatarUrl = computed(() => {
  if (userStore.avatar) {
    if (userStore.avatar.startsWith('/uploads')) {
      return `http://localhost:8081${userStore.avatar}`
    }
    return userStore.avatar
  }
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(userStore.username || 'User')}&background=2563eb&color=fff&size=128`
})

const sidebarClass = computed(() => [
  'fixed lg:sticky top-16 left-0 z-40 w-64 h-[calc(100vh-4rem)] bg-white border-r border-gray-200 overflow-y-auto transition-transform duration-300',
  visible.value ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
])

function close() {
  visible.value = false
}

function handleResize() {
  isMobile.value = window.innerWidth < 1024
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))
</script>