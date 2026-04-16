import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AIAssistant from '../views/AIAssistant.vue'
import FlowList from '../views/FlowList.vue'
import FlowDetail from '../views/FlowDetail.vue'

const routes = [
  {
    path: '/',
    name: 'AIAssistant',
    component: AIAssistant
  },
  {
    path: '/ai-assistant',
    name: 'AIAssistant',
    component: AIAssistant
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/flow-list',
    name: 'FlowList',
    component: FlowList
  },
  {
    path: '/flow-detail/:id',
    name: 'FlowDetail',
    component: FlowDetail
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
