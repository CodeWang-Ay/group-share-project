import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import { getLoginUrl } from '../config'
import Dashboard from '../views/Dashboard.vue'
import MeetingSchedule from '../views/MeetingSchedule.vue'
import ReportMaterials from '../views/ReportMaterials.vue'
import MeetingRecord from '../views/MeetingRecord.vue'
import UserManagement from '../views/UserManagement.vue'
import AcademicTools from '../views/AcademicTools.vue'
import ResearchProgress from '../views/ResearchProgress.vue'
import ResearchTasks from '../views/ResearchTasks.vue'
import ShareFile from '../views/ShareFile.vue'
import PaperDatabase from '../views/PaperDatabase.vue'
import UserProfile from '../views/UserProfile.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/meeting-schedule',
    name: 'MeetingSchedule',
    component: MeetingSchedule
  },
  {
    path: '/report-materials',
    name: 'ReportMaterials',
    component: ReportMaterials
  },
  {
    path: '/meeting-record',
    name: 'MeetingRecord',
    component: MeetingRecord
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: UserManagement
  },
  {
    path: '/academic-tools',
    name: 'AcademicTools',
    component: AcademicTools
  },
  {
    path: '/research-progress',
    name: 'ResearchProgress',
    component: ResearchProgress
  },
  {
    path: '/research-tasks',
    name: 'ResearchTasks',
    component: ResearchTasks
  },
  {
    path: '/share-file',
    name: 'ShareFile',
    component: ShareFile
  },
  {
    path: '/paper-database',
    name: 'PaperDatabase',
    component: PaperDatabase
  },
  {
    path: '/user-profile',
    name: 'UserProfile',
    component: UserProfile
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局路由守卫：未登录用户重定向到登录页
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 如果 URL 中有 session_token 参数，说明刚从登录页回来，允许通过
  const urlToken = new URLSearchParams(window.location.search).get('session_token')
  if (urlToken) {
    next()
    return
  }

  if (!userStore.isLoggedIn) {
    window.location.href = getLoginUrl()
    return
  }
  next()
})

export default router