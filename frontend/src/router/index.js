import { createRouter, createWebHistory } from 'vue-router'

// 11 个模块路由（对应 PRD 全部页面）
const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '工作台总览', icon: '▦' } },
  { path: '/workflows', name: 'workflows', component: () => import('../views/WorkflowsView.vue'), meta: { title: '工作流列表', icon: '📋' } },
  { path: '/editor', name: 'editor', component: () => import('../views/EditorView.vue'), meta: { title: '编排画布', icon: '✎' } },
  { path: '/runs', name: 'runs', component: () => import('../views/RunsView.vue'), meta: { title: '执行追踪', icon: '▶' } },
  { path: '/assets', name: 'assets', component: () => import('../views/AssetsView.vue'), meta: { title: '认证资产库', icon: '🏅' } },
  { path: '/tasks', name: 'tasks', component: () => import('../views/TasksView.vue'), meta: { title: '异步任务', icon: '⏳' } },
  { path: '/models', name: 'models', component: () => import('../views/ModelsView.vue'), meta: { title: '模型与额度', icon: '🧠' } },
  { path: '/audit', name: 'audit', component: () => import('../views/AuditView.vue'), meta: { title: '审计账本', icon: '🔒' } },
  { path: '/capabilities', name: 'capabilities', component: () => import('../views/CapabilitiesView.vue'), meta: { title: '开放能力', icon: '🌐' } },
  { path: '/resources', name: 'resources', component: () => import('../views/ResourcesView.vue'), meta: { title: '资源与锁', icon: '🗄️' } },
  { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { title: '配置中心', icon: '⚙️' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router