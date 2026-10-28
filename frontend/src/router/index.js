import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// 11 个模块路由（对应 PRD 全部页面）+ 登录页
const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { title: '登录', noLayout: true, requiresAuth: false } },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '工作台总览', icon: '▦', requiresAuth: true, noLayout: true } },
  { path: '/workflows', name: 'workflows', component: () => import('../views/WorkflowsView.vue'), meta: { title: '工作流列表', icon: '📋', requiresAuth: true } },
  { path: '/editor', name: 'editor', component: () => import('../views/EditorView.vue'), meta: { title: '编排画布', icon: '✎', requiresAuth: true } },
  { path: '/runs', name: 'runs', component: () => import('../views/RunsView.vue'), meta: { title: '执行追踪', icon: '▶', requiresAuth: true } },
  { path: '/assets', name: 'assets', component: () => import('../views/AssetsView.vue'), meta: { title: '认证资产库', icon: '🏅', requiresAuth: true } },
  { path: '/tasks', name: 'tasks', component: () => import('../views/TasksView.vue'), meta: { title: '异步任务', icon: '⏳', requiresAuth: true } },
  { path: '/models', name: 'models', component: () => import('../views/ModelsView.vue'), meta: { title: '模型与额度', icon: '🧠', requiresAuth: true } },
  { path: '/audit', name: 'audit', component: () => import('../views/AuditView.vue'), meta: { title: '审计账本', icon: '🔒', requiresAuth: true } },
  { path: '/capabilities', name: 'capabilities', component: () => import('../views/CapabilitiesView.vue'), meta: { title: '开放能力', icon: '🌐', requiresAuth: true } },
  { path: '/resources', name: 'resources', component: () => import('../views/ResourcesView.vue'), meta: { title: '资源与锁', icon: '🗄️', requiresAuth: true } },
  { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { title: '配置中心', icon: '⚙️', requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 前端 mock 鉴权守卫：未登录 → /login；已登录访问 /login → /dashboard
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: to.path !== '/' ? { redirect: to.path } : {} }
  }
  if (to.path === '/login' && auth.isLoggedIn) {
    return { path: '/dashboard' }
  }
  return true
})

export default router
