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
        <router-link to="/user-profile" class="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer">
          <img :src="avatarUrl"
               class="w-12 h-12 rounded-full border-2 border-white shadow-sm object-cover">
          <div>
            <p class="font-semibold text-gray-800">{{ userStore.username }}</p>
            <span class="text-sm bg-primary text-white px-2 py-0.5 rounded-full">
              {{ userStore.roleText }}
            </span>
          </div>
        </router-link>
      </div>

      <!-- 个人中心菜单（个人资料/修改密码/设置页面） -->
      <nav v-if="isPersonalPage">
        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3">个人中心</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-user-o" text="个人资料" to="/user-profile" :active="currentRoute === '/user-profile'" />
          <MenuItem icon="fa-key" text="修改密码" to="/edit-password" :active="currentRoute === '/edit-password'" />
          <MenuItem icon="fa-cog" text="设置" to="/settings" :active="currentRoute === '/settings'" />
          <MenuItem icon="fa-reply" text="返回主页面" to="/" />
        </ul>
      </nav>

      <!-- 常规菜单 -->
      <nav v-else>
        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3">组会管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-dashboard" text="工作台" to="/" />
          <MenuItem icon="fa-calendar" text="组会安排" to="/meeting-schedule" />
          <MenuItem icon="fa-file-text-o" text="汇报材料" to="/report-materials" />
          <MenuItem icon="fa-comments-o" text="组会记录" to="/meeting-record" />
        </ul>

        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3 mt-6">资源管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-book" text="学术文献" to="/paper-database" />
          <MenuItem icon="fa-folder-open-o" text="共享资料" to="/share-file" />
          <MenuItem icon="fa-tasks" text="研究任务" to="/research-tasks" />
        </ul>

        <p class="text-xs uppercase text-gray-500 font-medium mb-2 px-3 mt-6">团队管理</p>
        <ul class="space-y-1">
          <MenuItem icon="fa-users" text="成员管理" to="/user-management" />
          <MenuItem icon="fa-graduation-cap" text="学术工具" to="/academic-tools" />
          <MenuItem icon="fa-line-chart" text="研究进展" to="/research-progress" />
        </ul>
      </nav>
    </div>
  </aside>

  <div v-if="visible && isMobile" @click="close" class="fixed inset-0 bg-black/50 z-30 lg:hidden"></div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import MenuItem from './MenuItem.vue'
import { getAvatarUrl } from '../config'

const route = useRoute()
const userStore = useUserStore()
const visible = defineModel()

const isMobile = ref(window.innerWidth < 1024)

// 当前路由路径
const currentRoute = computed(() => route.path)

// 是否是个人中心页面
const isPersonalPage = computed(() => {
  return currentRoute.value === '/user-profile' || currentRoute.value === '/edit-password' || currentRoute.value === '/settings'
})

// 头像URL处理
const avatarUrl = computed(() => getAvatarUrl(userStore.avatar, userStore.username))

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