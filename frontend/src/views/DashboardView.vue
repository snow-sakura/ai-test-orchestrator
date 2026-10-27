<template>
  <div class="space-y-6">
    <!-- 页头（竞品对齐：page-header / page-title） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">工作台总览</h1>
        <p class="text-xs text-polaroid-warm-500 mt-0.5">
          {{ pendingCount }} 项待办审批 · {{ runningCount }} 个运行进行中
        </p>
      </div>
      <button @click="goTo('/workflows')" class="px-4 py-2 bg-polaroid-warm-500 text-white text-sm rounded-lg hover:bg-polaroid-warm-600 shadow-sm transition-colors">＋ 新建工作流</button>
    </div>

    <!-- KPI 卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="kpi in kpis" :key="kpi.label" class="polaroid-card rounded-lg p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs opacity-60">{{ kpi.label }}</span>
          <span class="text-lg">{{ kpi.icon }}</span>
        </div>
        <div class="text-2xl font-bold mt-2 text-polaroid-warm-800">{{ kpi.value }}</div>
        <div class="text-[11px] mt-1" :class="kpi.trend >= 0 ? 'text-green-600' : 'text-red-500'">
          {{ kpi.trend >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.trend) }}% <span class="opacity-50">较上周</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-4">
      <!-- 最近运行 -->
      <div class="polaroid-card rounded-lg col-span-2">
        <div class="flex items-center justify-between p-4 border-b border-polaroid-warm-200">
          <h3 class="font-semibold text-sm">最近运行</h3>
          <button @click="goTo('/runs')" class="text-xs text-polaroid-warm-600 hover:text-polaroid-warm-800">查看全部 →</button>
        </div>
        <div class="divide-y divide-polaroid-warm-100">
          <div v-for="run in recentRuns" :key="run.id" class="flex items-center gap-3 p-3 hover:bg-polaroid-warm-50 cursor-pointer" @click="goTo('/runs')">
            <span class="w-2 h-2 rounded-full shrink-0" :class="runStatusColor(run.status)"></span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">{{ run.wfName }}</div>
              <div class="text-[11px] opacity-50">{{ run.trigger }} · {{ run.started }} · {{ run.dur }}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-xs font-medium" :class="run.gate ? 'text-polaroid-warm-700' : ''">{{ run.gate || run.status }}</div>
              <div class="text-[11px] opacity-50">¥{{ run.cost }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 待我处理 -->
      <div class="polaroid-card rounded-lg">
        <div class="p-4 border-b border-polaroid-warm-200">
          <h3 class="font-semibold text-sm">待我处理</h3>
        </div>
        <div class="divide-y divide-polaroid-warm-100">
          <div v-for="todo in todos" :key="todo.id" class="p-3 flex items-center gap-3 cursor-pointer hover:bg-polaroid-warm-50" @click="goTo(todo.route)">
            <span class="text-lg">{{ todo.icon }}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium">{{ todo.title }}</div>
              <div class="text-[11px] opacity-50">{{ todo.detail }}</div>
            </div>
            <button class="text-xs px-2 py-1 bg-polaroid-warm-200 rounded hover:bg-polaroid-warm-300 shrink-0">处理</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编排范式入口 -->
    <div class="polaroid-card rounded-lg">
      <div class="p-4 border-b border-polaroid-warm-200">
        <h3 class="font-semibold text-sm">典型编排范式</h3>
        <p class="text-[11px] opacity-50 mt-0.5">从 PRD §8 五大范式快速开始</p>
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-4 p-4">
        <div v-for="p in paradigms" :key="p.id" class="border border-polaroid-warm-200 rounded-lg p-3 hover:border-polaroid-warm-400 hover:shadow-sm cursor-pointer transition-all" @click="goTo('/workflows')">
          <div class="text-xl mb-2">{{ p.icon }}</div>
          <div class="text-sm font-medium">{{ p.name }}</div>
          <div class="text-[11px] opacity-50 mt-1">{{ p.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const kpis = ref([])
const recentRuns = ref([])
const todos = ref([])
const paradigms = ref([])
const pendingCount = ref(0)
const runningCount = ref(0)

const fallbackParadigms = [
  { id: 'cicd', name: 'CI/CD 质量门禁', icon: '🚦', desc: '变更→执行→门禁' },
  { id: 'explore', name: '智能探索回归', icon: '🕵️', desc: '浏览器智能体+异步' },
  { id: 'mobile', name: '移动端多端回归', icon: '📱', desc: '设备并行+资源锁' },
  { id: 'design', name: '需求到用例', icon: '🧩', desc: '解析→生成→认证' },
  { id: 'external', name: '外部智能体按需', icon: '🌐', desc: '鉴权→触发→回调' },
]

onMounted(async () => {
  try {
    const res = await axios.get('/api/dashboard/summary')
    const data = res.data
    kpis.value = data.kpis
    recentRuns.value = data.recentRuns
    todos.value = data.todos
    paradigms.value = data.paradigms || fallbackParadigms
    pendingCount.value = data.pendingCount
    runningCount.value = data.runningCount
  } catch (e) {
    // 后端未启动时使用本地回退数据，保证页面可用
    kpis.value = [
      { label: '工作流总数', value: '8', icon: '📋', trend: 14 },
      { label: '今日运行', value: '42', icon: '▶', trend: 8 },
      { label: '通过率', value: '91%', icon: '✅', trend: 3 },
      { label: '本月成本', value: '¥2,380', icon: '💸', trend: -6 },
    ]
    recentRuns.value = [
      { id: 'r1', wfName: '代码变更驱动的 CI/CD 质量门禁', status: 'success', trigger: 'Git Push', started: '10-26 16:42', dur: '6m18s', cost: 4.82, gate: '有条件通过' },
      { id: 'r2', wfName: '核心接口每日巡检', status: 'success', trigger: '定时', started: '10-26 09:00', dur: '2m05s', cost: 1.20, gate: '通过' },
      { id: 'r3', wfName: '移动端多端回归', status: 'failed', trigger: '手动', started: '10-25 21:33', dur: '4m40s', cost: 3.10, gate: '阻断' },
      { id: 'r4', wfName: '安全基线扫描流水线', status: 'running', trigger: 'Git Push', started: '10-25 15:20', dur: '进行中', cost: 0.85, gate: '' },
    ]
    todos.value = [
      { id: 't1', icon: '✋', title: '人工审批门', detail: '工作流 wf_cicd · 高风险变更', route: '/runs' },
      { id: 't2', icon: '📮', title: '缺陷归档确认', detail: '3 条待确认缺陷', route: '/assets' },
      { id: 't3', icon: '🔑', title: '能力接入审批', detail: '2 项外部调用待审批', route: '/capabilities' },
    ]
    paradigms.value = fallbackParadigms
    pendingCount.value = 5
    runningCount.value = 2
  }
})

function runStatusColor(status) {
  return {
    success: 'bg-green-500',
    failed: 'bg-red-500',
    running: 'bg-amber-400',
  }[status] || 'bg-gray-400'
}

function goTo(path) {
  router.push(path)
}
</script>