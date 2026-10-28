<template>
  <div class="space-y-4">
    <!-- 页头（竞品对齐：page-header / page-title / header-actions） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">执行追踪</h1>
        <p class="text-xs text-competitor-text-2 mt-0.5">
          共 {{ filteredRuns.length }} 条运行记录 · 支持按工作流 / 状态筛选 · 节点级时间线与门禁裁决
        </p>
      </div>
      <div class="header-actions">
        <select
          v-model="filterWorkflow"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部工作流</option>
          <option v-for="wf in workflowNames" :key="wf" :value="wf">{{ wf }}</option>
        </select>
        <select
          v-model="filterStatus"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部状态</option>
          <option value="completed">已完成</option>
          <option value="running">运行中</option>
          <option value="failed">失败</option>
        </select>
      </div>
    </div>

    <!-- 筛选快捷标签 -->
    <div class="flex items-center gap-2">
      <button
        v-for="s in statusTabs"
        :key="s.key"
        @click="filterStatus = s.key"
        :class="filterStatus === s.key ? 'bg-competitor-primary text-white' : 'bg-competitor-main text-competitor-text hover:bg-competitor-border'"
        class="px-3 py-1 text-xs rounded-full transition-colors"
      >{{ s.label }}{{ filterStatus === s.key && s.key === '' ? `（${runs.length}）` : '' }}</button>
      <span v-if="filterStatus !== '' || filterWorkflow !== ''" class="text-xs text-competitor-text-2">
        已筛选 {{ filteredRuns.length }} 条
      </span>
    </div>

    <!-- 运行列表 -->
    <div class="space-y-3">
      <div
        v-for="run in filteredRuns"
        :key="run.id"
        :class="selectedRun?.id === run.id ? 'ring-2 ring-competitor-primary' : ''"
        class="polaroid-card rounded-lg p-4 cursor-pointer transition-shadow hover:shadow-md"
        @click="selectRun(run)"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span
                class="w-2 h-2 rounded-full shrink-0"
                :class="runStatusColor(run.status)"
              ></span>
              <h3 class="font-semibold text-sm text-competitor-text truncate">
                {{ run.workflow_name || run.workflow_id }}
              </h3>
              <span
                class="status-tag shrink-0"
                :class="runStatusBadge(run.status)"
              >{{ runStatusLabel(run.status) }}</span>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-competitor-main text-competitor-text-2 shrink-0">
                {{ run.trigger }}
              </span>
            </div>
            <div class="text-[11px] text-competitor-text-2 mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
              <span>🕐 {{ run.started }}</span>
              <span>⏱ {{ run.duration }}</span>
              <span>🧠 Token {{ run.tokens?.toLocaleString?.() || run.tokens || 0 }}</span>
              <span>💸 ¥{{ run.cost?.toFixed?.(4) || 0 }}</span>
              <span v-if="run.gate?.verdict" class="text-competitor-success font-medium">
                门禁：{{ run.gate.verdict }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              @click.stop="selectRun(run)"
              class="text-xs px-2 py-1 border border-competitor-border rounded hover:bg-competitor-main"
            >查看</button>
            <button
              @click.stop="triggerRun(run)"
              class="text-xs px-2 py-1 bg-competitor-primary text-white rounded hover:bg-competitor-primary-dark"
            >重新运行</button>
          </div>
        </div>
      </div>
      <div v-if="filteredRuns.length === 0" class="card-container p-10 text-center text-competitor-text-2 text-sm">
        暂无匹配的运行记录
      </div>
    </div>

    <!-- 运行详情（节点级时间线 + 执行面板 + 门禁裁决） -->
    <div v-if="selectedRun" class="card-container">
      <!-- 详情头部 -->
      <div class="flex items-center justify-between p-4 border-b border-competitor-border">
        <div>
          <h3 class="font-bold text-competitor-text">运行详情</h3>
          <p class="text-[11px] text-competitor-text-2 mt-0.5">{{ selectedRun.id }}</p>
        </div>
        <button @click="selectedRun = null" class="text-xl leading-none opacity-50 hover:opacity-100">&times;</button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
        <!-- 节点级时间线（PRD §7.4） -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-semibold text-sm">节点级时间线（PRD §7.4）</h4>
            <button @click="refreshSelectedRun" class="text-xs text-competitor-primary hover:text-competitor-primary-dark">↻ 刷新</button>
          </div>
          <div class="space-y-0 relative max-h-120 overflow-y-auto pr-2">
            <div
              v-for="(item, idx) in selectedRun.timeline"
              :key="item.nodeId + '-' + item.seq"
              class="relative pl-8 pb-4"
            >
              <!-- 时间线竖线 -->
              <div v-if="idx < selectedRun.timeline.length - 1" class="absolute left-2.5 top-6 bottom-0 w-0.5 bg-competitor-border"></div>
              <!-- 节点圆点 -->
              <div
                class="absolute left-0 top-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold"
                :class="nodeStatusClass(item.status)"
              >{{ item.seq }}</div>
              <!-- 节点卡片 -->
              <div class="rounded-lg border border-competitor-border bg-white p-3 space-y-1.5">
                <div class="flex items-center justify-between">
                  <div class="font-semibold text-sm text-competitor-text">{{ item.label }}</div>
                  <span :class="nodeStatusText(item.status)" class="text-[10px] px-2 py-0.5 rounded-full bg-competitor-main">
                    {{ nodeStatusLabel(item.status) }}
                  </span>
                </div>
                <div class="text-[11px] text-competitor-text-2 flex flex-wrap gap-x-3">
                  <span>{{ item.model }}</span>
                  <span>⏱ {{ item.duration }}</span>
                  <span>🧠 {{ item.tokens }}</span>
                  <span>💸 ¥{{ item.cost?.toFixed?.(4) }}</span>
                </div>
                <!-- 展开详情 -->
                <div v-if="expandedNodes[item.nodeId]" class="space-y-2 mt-2 border-t border-competitor-border/60 pt-2">
                  <div>
                    <div class="text-[10px] font-medium text-competitor-text-2 mb-1">推理摘要</div>
                    <div class="text-xs text-competitor-text">{{ item.reasoning || '—' }}</div>
                  </div>
                  <div v-if="item.tools?.length">
                    <div class="text-[10px] font-medium text-competitor-text-2 mb-1">工具调用</div>
                    <div class="flex flex-wrap gap-1">
                      <span v-for="t in item.tools" :key="t" class="px-2 py-0.5 text-[10px] bg-competitor-main rounded-full">{{ t }}</span>
                    </div>
                  </div>
                  <div>
                    <div class="text-[10px] font-medium text-competitor-text-2 mb-1">输入绑定</div>
                    <div class="text-xs text-competitor-text font-mono">{{ JSON.stringify(item.input?.payload || item.input || {}) }}</div>
                  </div>
                  <div>
                    <div class="text-[10px] font-medium text-competitor-text-2 mb-1">输出结果</div>
                    <div class="text-xs text-competitor-text font-mono break-all">{{ JSON.stringify(item.output || {}) }}</div>
                  </div>
                  <div v-if="item.evidence?.length">
                    <div class="text-[10px] font-medium text-competitor-text-2 mb-1">证据引用</div>
                    <div class="flex flex-wrap gap-1">
                      <span v-for="ev in item.evidence" :key="ev" class="px-2 py-0.5 text-[10px] bg-competitor-main border border-competitor-border rounded-full">
                        {{ ev }}
                      </span>
                    </div>
                  </div>
                  <div v-if="item.gate" class="rounded bg-competitor-main border border-competitor-border p-2 mt-1">
                    <div class="text-[11px] font-medium text-competitor-text">门禁裁决（确定性引擎）</div>
                    <div class="text-xs text-competitor-text mt-0.5">判定：{{ item.gate.verdict }} · 引擎：{{ item.gate.engine }}</div>
                    <div class="text-[11px] text-competitor-text-2 mt-0.5">归因叙述（模型）：{{ item.gate.narrative }}</div>
                  </div>
                </div>
                <button
                  @click="toggleNode(item.nodeId)"
                  class="text-xs text-competitor-text-2 hover:text-competitor-text mt-1"
                >{{ expandedNodes[item.nodeId] ? '收起详情' : '展开执行面板' }}</button>
              </div>
            </div>
            <div v-if="!selectedRun.timeline?.length" class="text-xs text-competitor-text-2 pl-8">该运行暂无节点级时间线</div>
          </div>
        </div>

        <!-- 右侧：门禁裁决 + 执行日志 -->
        <div class="space-y-4">
          <!-- 门禁裁决区（确定性判定 + 归因叙述分离，PRD 原则五） -->
          <div class="rounded-lg border border-competitor-border bg-competitor-main p-4">
            <div class="font-semibold text-sm text-competitor-text mb-2">门禁裁决区（PRD 原则五）</div>
            <template v-if="selectedRun.gate">
              <div class="space-y-2">
                <div>
                  <div class="text-[10px] font-medium text-competitor-text-2">确定性判定（规则引擎）</div>
                  <div class="text-lg font-bold" :class="selectedRun.gate.verdict === '通过' ? 'text-competitor-success' : 'text-competitor-danger'">
                    {{ selectedRun.gate.verdict }}
                  </div>
                </div>
                <div>
                  <div class="text-[10px] font-medium text-competitor-text-2">归因叙述（模型生成，不得覆盖判定）</div>
                  <div class="text-xs text-competitor-text">{{ selectedRun.gate.narrative }}</div>
                </div>
                <div>
                  <div class="text-[10px] font-medium text-competitor-text-2">裁决引擎</div>
                  <div class="text-xs text-competitor-text">{{ selectedRun.gate.engine }}</div>
                </div>
              </div>
            </template>
            <div v-else class="text-xs text-competitor-text-2">该运行未触发门禁节点</div>
          </div>

          <!-- 执行日志（PRD §7.4） -->
          <div class="rounded-lg border border-competitor-border p-4">
            <div class="font-semibold text-sm text-competitor-text mb-2">执行日志（PRD §7.4）</div>
            <div class="space-y-1 max-h-60 overflow-y-auto">
              <div
                v-for="(log, i) in selectedRun.logs || []"
                :key="i"
                class="flex gap-2 text-xs"
              >
                <span class="text-competitor-text-2 shrink-0 font-mono">{{ log.time }}</span>
                <span class="text-competitor-text">{{ log.msg }}</span>
              </div>
              <div v-if="!selectedRun.logs?.length" class="text-xs text-competitor-text-2">暂无日志</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 right-6 z-50 px-4 py-2 bg-competitor-navy text-white text-sm rounded-lg shadow-lg">
      {{ toast }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const runs = ref([])
const selectedRun = ref(null)
const filterWorkflow = ref('')
const filterStatus = ref('')
const expandedNodes = ref({})
const toast = ref('')

const statusTabs = [
  { key: '', label: '全部' },
  { key: 'completed', label: '已完成' },
  { key: 'running', label: '运行中' },
  { key: 'failed', label: '失败' },
]

const workflowNames = computed(() => {
  const names = new Set(runs.value.map(r => r.workflow_name || r.workflow_id).filter(Boolean))
  return [...names]
})

const filteredRuns = computed(() => {
  return runs.value.filter(r => {
    if (filterWorkflow.value && r.workflow_name !== filterWorkflow.value && r.workflow_id !== filterWorkflow.value) return false
    if (filterStatus.value && r.status !== filterStatus.value) return false
    return true
  })
})

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

function runStatusColor(status) {
  return { completed: 'bg-competitor-success', running: 'bg-competitor-warning', failed: 'bg-competitor-danger' }[status] || 'bg-gray-400'
}
function runStatusLabel(status) {
  return { completed: '已完成', running: '运行中', failed: '失败' }[status] || status
}
function runStatusBadge(status) {
  return { completed: 'bg-green-100 text-green-700', running: 'bg-amber-100 text-amber-700', failed: 'bg-red-100 text-red-700' }[status] || 'bg-gray-100 text-gray-700'
}
function nodeStatusClass(status) {
  return { success: 'bg-competitor-success text-white', running: 'bg-competitor-warning text-white', failed: 'bg-competitor-danger text-white', pending: 'bg-gray-300 text-gray-600' }[status] || 'bg-gray-300 text-gray-600'
}
function nodeStatusText(status) {
  return { success: 'text-green-700', running: 'text-amber-700', failed: 'text-red-700', pending: 'text-gray-500' }[status] || 'text-gray-500'
}
function nodeStatusLabel(status) {
  return { success: '成功', running: '运行中', failed: '失败', pending: '待执行' }[status] || status
}

function toggleNode(nodeId) {
  expandedNodes.value[nodeId] = !expandedNodes.value[nodeId]
}

async function selectRun(run) {
  try {
    const res = await axios.get(`/api/runs/${run.id}`)
    selectedRun.value = res.data
    expandedNodes.value = {}
  } catch (e) {
    selectedRun.value = run
  }
}

async function refreshSelectedRun() {
  if (!selectedRun.value) return
  try {
    const res = await axios.get(`/api/runs/${selectedRun.value.id}`)
    selectedRun.value = res.data
  } catch (e) { /* 保持现状 */ }
}

async function triggerRun(run) {
  try {
    const res = await axios.post(`/api/execute/${run.workflow_id}`)
    showToast('已触发运行，正在跳转执行追踪…')
    await new Promise(r => setTimeout(r, 1500))
    await refresh()
  } catch (e) {
    showToast('触发失败：' + (e.message || e))
  }
}

async function refresh() {
  try {
    const res = await axios.get('/api/runs')
    runs.value = res.data || []
    if (selectedRun.value) {
      const s = runs.value.find(r => r.id === selectedRun.value.id)
      if (s) selectedRun.value = { ...selectedRun.value, ...s }
    }
  } catch (e) {
    console.error('加载运行记录失败', e)
  }
}

onMounted(refresh)
</script>
