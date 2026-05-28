import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import MeetingSchedule from '../views/MeetingSchedule.vue'
import ReportMaterials from '../views/ReportMaterials.vue'
import MeetingRecord from '../views/MeetingRecord.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router