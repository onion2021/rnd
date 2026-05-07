import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AIAssistant from '../views/AIAssistant.vue'
import FlowList from '../views/FlowList.vue'
import FlowDetail from '../views/FlowDetail.vue'
import DOEComparison from '../views/DOEComparison.vue'
import DOEDesignAssistant from '../views/DOEDesignAssistant.vue'

const routes = [
  {
    path: '/',
    redirect: '/ai-assistant'
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
    path: '/doe-comparison',
    name: 'DOEComparison',
    component: DOEComparison
  },
  {
    path: '/doe-design',
    name: 'DOEDesignAssistant',
    component: DOEDesignAssistant
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
