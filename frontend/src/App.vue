<template>
  <!-- 竞品布局壳：100vh 固定视口，主区 padding 20px + overflow-y auto（1920×1080 无页面级滚动） -->
  <!-- 登录页 / 首页（meta.noLayout）不渲染侧栏壳，直接渲染路由视图 -->
  <template v-if="route.meta.noLayout">
    <router-view />
  </template>
  <div v-else class="flex h-screen w-full overflow-hidden bg-competitor-main text-competitor-text">
    <!-- 左侧导航栏：240px 深蓝 #001529（竞品规格：.el-aside width 240px + 60px logo 区） -->
    <aside
      class="flex flex-col shrink-0 bg-competitor-navy text-white"
      style="width: 240px;"
    >
      <!-- Logo 区（竞品：60px 深底 + 下边框 #1f1f1f） -->
      <div class="h-[60px] px-4 border-b border-white/10 flex items-center gap-3 shrink-0">
        <div class="w-10 h-10 bg-competitor-primary rounded-lg flex items-center justify-center text-white text-base font-bold shadow-lg">
          AI
        </div>
        <div class="leading-tight">
          <div class="font-bold text-sm text-white">AI 测试编排</div>
          <div class="text-[10px] text-white/50 mt-0.5">智能体工作流平台</div>
        </div>
      </div>

      <!-- 模块分组导航菜单（竞品：14px 白字，激活 #1890ff 圆角） -->
      <nav class="flex-1 overflow-y-auto py-3 text-sm" style="scrollbar-width: none;">
        <div v-for="group in navGroups" :key="group.key" class="mb-2">
          <!-- 分组头（可展开，竞品 el-sub-menu 风格） -->
          <button
            @click="toggleGroup(group.key)"
            class="w-full flex items-center justify-between px-4 py-2.5 text-[13px] font-semibold text-white/60 hover:bg-white/5 transition-colors"
          >
            <span class="flex items-center gap-2.5">
              <span class="text-base">{{ group.icon }}</span>
              {{ group.name }}
            </span>
            <span class="text-[11px] opacity-40">{{ openGroups[group.key] ? '−' : '+' }}</span>
          </button>
          <!-- 分组内叶子项 -->
          <div v-show="openGroups[group.key]" class="px-3 space-y-1 pb-2">
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-[14px] transition-colors"
              :class="isActive(item.path) ? 'bg-competitor-primary text-white shadow-sm' : 'text-white/75 hover:bg-white/10'"
            >
              <span class="w-5 text-center text-base leading-none">{{ item.icon }}</span>
              <span class="truncate">{{ item.title }}</span>
            </router-link>
          </div>
        </div>
      </nav>

      <!-- 底部用户区（竞品 header-right 用户下拉风格） -->
      <div class="px-4 py-3.5 border-t border-white/10 flex items-center gap-2.5 shrink-0">
        <div class="w-8 h-8 rounded-full bg-competitor-primary flex items-center justify-center text-xs font-bold text-white shadow">雪</div>
        <div class="min-w-0 flex-1">
          <div class="text-[13px] font-medium text-white truncate">雪 樱</div>
          <div class="text-[11px] text-white/45 truncate">测试负责人</div>
        </div>
        <button @click="logout" class="text-white/40 hover:text-white text-sm px-1.5 py-1 rounded transition-colors" title="退出登录">⏻</button>
      </div>
    </aside>

    <!-- 右侧主内容区：纵向容器（顶栏 60px + 主区） -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶栏：60px 白底 + #e8e8e8 下边框，面包屑左 + 徽章右（竞品 .el-header） -->
      <header class="h-[60px] shrink-0 bg-white border-b border-competitor-border flex items-center justify-between px-5">
        <div class="flex items-center gap-2.5 text-sm min-w-0">
          <router-link
            to="/dashboard"
            class="text-competitor-primary hover:text-competitor-primary-dark transition-colors shrink-0 text-[14px]"
          >首页</router-link>
          <span v-if="currentModule" class="text-competitor-text-2 shrink-0">/</span>
          <span v-if="currentModule" class="text-competitor-text-2 truncate text-[14px]">{{ currentModule }}</span>
          <span v-if="currentModule && currentTitle && currentModule !== currentTitle" class="text-competitor-text-2 shrink-0">/</span>
          <span class="font-medium text-competitor-text truncate text-[14px]">{{ currentTitle }}</span>
        </div>
        <div class="flex items-center gap-3 text-xs text-competitor-text-2 shrink-0">
          <span class="px-2.5 py-1 bg-competitor-main rounded-full text-[12px]">环境：生产</span>
          <span class="px-2.5 py-1 bg-competitor-main rounded-full text-[12px]">v1.0.0</span>
        </div>
      </header>

      <!-- 主区：#f5f5f5 + padding 20px + overflow-y auto（竞品 .el-main），无页面级滚动 -->
      <div class="flex-1 overflow-y-auto overflow-x-hidden bg-competitor-main page-container">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// 3 模块分组（竞品对齐：模块分组侧栏）
const navGroups = [
  {
    key: 'orchestration',
    name: '测试编排',
    icon: '🧩',
    items: [
      { path: '/dashboard', title: '工作台总览', icon: '▦' },
      { path: '/workflows', title: '工作流列表', icon: '📋' },
      { path: '/editor', title: '编排画布', icon: '✎' },
      { path: '/runs', title: '执行追踪', icon: '▶' },
    ],
  },
  {
    key: 'assets',
    name: '质量资产',
    icon: '🏅',
    items: [
      { path: '/assets', title: '认证资产库', icon: '🏅' },
      { path: '/tasks', title: '异步任务', icon: '⏳' },
      { path: '/models', title: '模型与额度', icon: '🧠' },
    ],
  },
  {
    key: 'ops',
    name: '平台运维',
    icon: '🔧',
    items: [
      { path: '/audit', title: '审计账本', icon: '🔒' },
      { path: '/capabilities', title: '开放能力', icon: '🌐' },
      { path: '/resources', title: '资源与锁', icon: '🗄️' },
      { path: '/settings', title: '配置中心', icon: '⚙️' },
    ],
  },
]

// 分组展开状态（默认全部展开）
const openGroups = reactive({
  orchestration: true,
  assets: true,
  ops: true,
})

function toggleGroup(key) {
  openGroups[key] = !openGroups[key]
}

const currentTitle = computed(() => route.meta.title || 'AI 测试编排平台')

// 当前所属模块（面包屑第二级）
const currentModule = computed(() => {
  for (const g of navGroups) {
    if (g.items.some(item => item.path === route.path)) {
      return g.name
    }
  }
  return null
})

function isActive(path) {
  return route.path === path
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>
