<template>
  <!-- 竞品布局壳：h-screen 固定视口，主区内容区滚动（1920×1080 不出现页面级滚动） -->
  <!-- 登录页（meta.noLayout）不渲染侧栏壳，直接渲染路由视图 -->
  <template v-if="route.meta.noLayout">
    <router-view />
  </template>
  <div v-else class="flex h-screen w-full overflow-hidden bg-competitor-main text-competitor-text">
    <!-- 左侧导航栏：240px 深蓝 #001529（竞品规格），小屏抽屉 -->
    <aside
      class="flex flex-col shrink-0 bg-competitor-navy text-white transition-all duration-200"
      :class="drawerOpen ? 'w-56 relative z-30' : 'w-56 lg:w-56 max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:-translate-x-full max-lg:z-30'"
    >
      <!-- Logo 区（竞品：60px 深底 + 下边框） -->
      <div class="h-14 px-4 border-b border-black/20 flex items-center gap-2">
        <div class="w-8 h-8 bg-competitor-primary rounded-md flex items-center justify-center text-white text-sm font-bold shadow-sm">AI</div>
        <div class="leading-tight">
          <div class="font-bold text-sm text-white">AI 测试编排</div>
          <div class="text-[10px] text-white/50">智能体工作流平台</div>
        </div>
      </div>

      <!-- 模块分组导航菜单（竞品：14px 白字，激活 #1890ff） -->
      <nav class="flex-1 overflow-y-auto py-2 text-sm">
        <div v-for="group in navGroups" :key="group.key" class="mb-1.5">
          <!-- 分组头（可展开） -->
          <button
            @click="toggleGroup(group.key)"
            class="w-full flex items-center justify-between px-4 py-2 text-xs font-semibold text-white/55 hover:bg-white/5 transition-colors"
          >
            <span class="flex items-center gap-2">
              <span class="text-sm">{{ group.icon }}</span>
              {{ group.name }}
            </span>
            <span class="text-[10px] opacity-50">{{ openGroups[group.key] ? '−' : '+' }}</span>
          </button>
          <!-- 分组内叶子项 -->
          <div v-show="openGroups[group.key]" class="px-2 space-y-0.5 pb-1.5">
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors"
              :class="isActive(item.path) ? 'bg-competitor-primary text-white shadow-sm' : 'text-white/75 hover:bg-white/10'"
            >
              <span class="w-5 text-center text-base leading-none">{{ item.icon }}</span>
              <span>{{ item.title }}</span>
            </router-link>
          </div>
        </div>
      </nav>

      <!-- 底部用户区 -->
      <div class="px-4 py-3 border-t border-black/20 flex items-center gap-2">
        <div class="w-7 h-7 rounded-full bg-competitor-primary flex items-center justify-center text-xs font-bold">雪</div>
        <div class="min-w-0">
          <div class="text-xs font-medium text-white truncate">雪 樱</div>
          <div class="text-[10px] text-white/50 truncate">测试负责人</div>
        </div>
      </div>
    </aside>

    <!-- 右侧主内容区：纵向容器（顶栏 + 主区） -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶栏：60px 白底 + #e8e8e8 下边框，面包屑左 + 语言/版本徽章右 -->
      <header class="h-14 shrink-0 bg-white border-b border-competitor-border flex items-center justify-between px-5">
        <div class="flex items-center gap-2 text-sm min-w-0">
          <!-- 抽屉触发（小屏） -->
          <button @click="drawerOpen = !drawerOpen" class="lg:hidden text-competitor-primary text-lg leading-none">≡</button>
          <router-link
            to="/dashboard"
            class="text-competitor-primary hover:text-competitor-primary-dark transition-colors shrink-0"
          >首页</router-link>
          <span v-if="currentModule" class="text-competitor-text-2 shrink-0">/</span>
          <span v-if="currentModule" class="text-competitor-text-2 truncate">{{ currentModule }}</span>
          <span v-if="currentModule && currentTitle && currentModule !== currentTitle" class="text-competitor-text-2 shrink-0">/</span>
          <span class="font-medium text-competitor-text truncate">{{ currentTitle }}</span>
        </div>
        <div class="flex items-center gap-2 text-xs text-competitor-text-2">
          <span class="px-2 py-1 bg-competitor-main rounded-full">环境：生产</span>
          <span class="px-2 py-1 bg-competitor-main rounded-full">v1.0.0</span>
        </div>
      </header>

      <!-- 主区：#f5f5f5，固定高度内容区滚动（calc(100vh - 顶栏 60px)），无页面级滚动 -->
      <div class="flex-1 overflow-auto page-container bg-competitor-main">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const drawerOpen = ref(false)

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
</script>
