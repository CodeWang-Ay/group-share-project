import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import MeetingSchedule from '../views/MeetingSchedule.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router