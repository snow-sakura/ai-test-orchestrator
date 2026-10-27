<template>
  <div class="flex h-screen w-full overflow-hidden bg-polaroid-warm-100 text-polaroid-warm-900">
    <!-- 左侧侧边导航栏 -->
    <aside class="w-56 shrink-0 border-r border-polaroid-warm-200 bg-white flex flex-col">
      <!-- Logo -->
      <div class="p-4 border-b border-polaroid-warm-200 flex items-center gap-2">
        <div class="w-8 h-8 bg-polaroid-warm-500 rounded-md flex items-center justify-center text-white text-sm font-bold shadow-sm">AI</div>
        <div class="leading-tight">
          <div class="font-bold text-sm">AI 测试编排</div>
          <div class="text-[10px] opacity-50">智能体工作流平台</div>
        </div>
      </div>

      <!-- 导航菜单 -->
      <nav class="flex-1 overflow-y-auto p-3 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors"
          :class="isActive(item.path) ? 'bg-polaroid-warm-500 text-white shadow-sm' : 'hover:bg-polaroid-warm-100 text-polaroid-warm-800'"
        >
          <span class="w-5 text-center text-base leading-none">{{ item.icon }}</span>
          <span>{{ item.title }}</span>
        </router-link>
      </nav>

      <!-- 底部用户区 -->
      <div class="p-4 border-t border-polaroid-warm-200 flex items-center gap-2">
        <div class="w-7 h-7 rounded-full bg-polaroid-warm-300 flex items-center justify-center text-xs font-bold">雪</div>
        <div>
          <div class="text-xs font-medium">雪 樱</div>
          <div class="text-[10px] opacity-50">测试负责人</div>
        </div>
      </div>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- 顶栏 -->
      <header class="h-14 shrink-0 border-b border-polaroid-warm-200 bg-white/80 backdrop-blur-sm flex items-center justify-between px-6">
        <div class="flex items-center gap-3">
          <h1 class="font-bold text-lg text-polaroid-warm-800">{{ currentTitle }}</h1>
        </div>
        <div class="flex items-center gap-2 text-xs text-polaroid-warm-600">
          <span class="px-2 py-1 bg-polaroid-warm-100 rounded-full">环境：生产</span>
          <span class="px-2 py-1 bg-polaroid-warm-100 rounded-full">v1.0.0</span>
        </div>
      </header>

      <!-- 路由出口 -->
      <div class="flex-1 overflow-auto">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/dashboard', title: '工作台总览', icon: '▦' },
  { path: '/workflows', title: '工作流列表', icon: '📋' },
  { path: '/editor', title: '编排画布', icon: '✎' },
  { path: '/runs', title: '执行追踪', icon: '▶' },
  { path: '/assets', title: '认证资产库', icon: '🏅' },
  { path: '/tasks', title: '异步任务', icon: '⏳' },
  { path: '/models', title: '模型与额度', icon: '🧠' },
  { path: '/audit', title: '审计账本', icon: '🔒' },
  { path: '/capabilities', title: '开放能力', icon: '🌐' },
  { path: '/resources', title: '资源与锁', icon: '🗄️' },
  { path: '/settings', title: '配置中心', icon: '⚙️' },
]

const currentTitle = computed(() => route.meta.title || 'AI 测试编排平台')

function isActive(path) {
  return route.path === path
}
</script>