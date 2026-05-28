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
      <div class="bg-primary/10 text-primary rounded-lg p-3 mb-6">
        <div class="flex items-center justify-between">
          <span class="font-medium">当前角色</span>
          <span class="text-sm bg-primary text-white px-2 py-1 rounded-full">
            {{ userStore.roleText }}
          </span>
        </div>
      </div>

      <nav>
        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3">组会管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-dashboard" text="工作台" active />
          <MenuItem icon="fa-calendar" text="组会安排" href="/gm_meeting_schedule" />
          <MenuItem icon="fa-file-text-o" text="汇报材料" href="/gm_report_materials" />
          <MenuItem icon="fa-comments-o" text="组会记录" href="/gm_meeting_record" />
        </ul>

        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3 mt-6">资源管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-book" text="学术文献" href="/rm_paper_database" />
          <MenuItem icon="fa-folder-open-o" text="共享资料" href="/rm_share_file" />
          <MenuItem icon="fa-tasks" text="研究任务" href="/rm_research_tasks" />
        </ul>

        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3 mt-6">团队管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-users" text="成员管理" href="/tm_user_management" />
          <MenuItem icon="fa-graduation-cap" text="学术工具" href="/tm_academic_website" />
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