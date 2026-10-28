<template>
  <div class="space-y-5">
    <!-- 页头（竞品对齐：page-header / page-title / header-actions） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">异步任务看板</h1>
        <p class="text-xs text-competitor-text-2 mt-0.5">
          共 {{ allTasks.length }} 项异步任务 · 支持轮询/回调、结果回写、超时与取消（PRD §6.4）
        </p>
      </div>
      <div class="header-actions">
        <button
          @click="openCreate"
          class="px-4 py-2 bg-competitor-primary text-white text-sm rounded-lg hover:bg-competitor-primary-dark transition-colors shadow-sm"
        >＋ 提交任务</button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <input
        v-model="search"
        placeholder="搜索任务名称..."
        class="w-56 p-2 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
      />
      <select v-model="filterType" class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white">
        <option value="">全部类型</option>
        <option v-for="t in taskTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
      </select>
      <select v-model="filterWorkflow" class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white">
        <option value="">全部工作流</option>
        <option v-for="w in workflowOptions" :key="w" :value="w">{{ w }}</option>
      </select>
      <select v-model="filterResource" class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white">
        <option value="">全部资源</option>
        <option v-for="r in resourceOptions" :key="r" :value="r">{{ r }}</option>
      </select>
      <span v-if="search || filterType || filterWorkflow || filterResource" class="text-xs text-competitor-text-2">
        已筛选 {{ filteredTasks.length }} 项
      </span>
    </div>

    <!-- 状态看板（PRD §6.4 全局任务看板：运行中 / 已完成 / 失败 / 超时） -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
      <div
        v-for="col in boardColumns"
        :key="col.key"
        class="card-container"
      >
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-competitor-text flex items-center gap-1.5">
            <span :class="col.dotClass"></span>
            {{ col.label }}
          </h3>
          <span class="text-xs px-2 py-0.5 rounded-full bg-competitor-main text-competitor-text-2">
            {{ tasksByStatus(col.key).length }}
          </span>
        </div>
        <div class="space-y-3 max-h-80 overflow-y-auto pr-1">
          <div
            v-for="task in tasksByStatus(col.key)"
            :key="task.id"
            @click="viewTask(task)"
            class="polaroid-card rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <h4 class="text-xs font-bold text-competitor-text truncate">{{ task.name }}</h4>
                <div class="text-[10px] text-competitor-text-2 mt-0.5">
                  {{ task.typeLabel }} · {{ task.workflow }} · {{ task.node }}
                </div>
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded-full shrink-0 bg-competitor-main text-competitor-text-2">
                {{ task.progress }}%
              </span>
            </div>
            <!-- 进度条 -->
            <div class="mt-2">
              <div class="h-1.5 bg-competitor-main rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :class="progressClass(col.key)"
                  :style="{ width: task.progress + '%' }"
                ></div>
              </div>
            </div>
            <!-- 资源锁 / 轮询回调 -->
            <div class="flex items-center justify-between mt-2 text-[10px] text-competitor-text-2">
              <span>🔒 {{ task.resource }}</span>
              <span>{{ task.modeLabel }} · {{ task.eta }}</span>
            </div>
            <!-- 操作 -->
            <div class="flex items-center gap-1.5 mt-2">
              <button
                @click.stop="viewTask(task)"
                class="text-[10px] px-2 py-0.5 border border-competitor-border rounded hover:bg-competitor-main"
              >查看</button>
              <button
                v-if="task.status === 'running'"
                @click.stop="cancelTask(task)"
                class="text-[10px] px-2 py-0.5 border border-red-200 text-competitor-danger rounded hover:bg-red-50"
              >取消</button>
              <button
                v-if="task.status === 'running'"
                @click.stop="pollTask(task)"
                class="text-[10px] px-2 py-0.5 bg-competitor-primary text-white rounded hover:bg-competitor-primary-dark"
              >轮询推进</button>
              <button
                v-if="task.status === 'running'"
                @click.stop="timeoutTask(task)"
                class="text-[10px] px-2 py-0.5 border border-amber-200 text-amber-600 rounded hover:bg-amber-50"
              >模拟超时</button>
            </div>
          </div>
          <div v-if="tasksByStatus(col.key).length === 0" class="text-xs text-competitor-text-2 text-center py-3">
            暂无 {{ col.label }} 任务
          </div>
        </div>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <div v-if="createModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-96 space-y-4">
        <h3 class="font-bold text-competitor-text">提交异步任务</h3>
        <label class="block text-xs font-medium text-competitor-text-2 mb-1">名称</label>
        <input v-model="newTask.name" class="w-full p-2 text-sm border border-competitor-border rounded outline-none focus:ring-1 focus:ring-competitor-primary" placeholder="任务名称" />
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">类型</label>
        <select v-model="newTask.type" class="w-full p-2 text-sm border border-competitor-border rounded outline-none">
          <option v-for="t in taskTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">工作流 ID</label>
        <input v-model="newTask.workflow" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" placeholder="wf_xxx" />
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">节点 ID</label>
        <input v-model="newTask.node" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" placeholder="n_xxx" />
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">资源</label>
        <input v-model="newTask.resource" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" placeholder="browser-farm-X" />
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-xs font-medium text-competitor-text-2 mb-1">轮询间隔(s)</label>
            <input v-model.number="newTask.poll_interval" type="number" min="0" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" />
          </div>
          <div>
            <label class="block text-xs font-medium text-competitor-text-2 mb-1">超时(s)</label>
            <input v-model.number="newTask.timeout_sec" type="number" min="1" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" />
          </div>
        </div>
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">模式</label>
        <select v-model="newTask.mode" class="w-full p-2 text-sm border border-competitor-border rounded outline-none">
          <option value="poll">轮询</option>
          <option value="callback">回调</option>
        </select>
        <div class="flex justify-end gap-2">
          <button @click="createModal = false" class="px-3 py-1.5 text-sm border border-competitor-border rounded-lg hover:bg-competitor-main">取消</button>
          <button @click="confirmCreate" class="px-4 py-1.5 text-sm bg-competitor-primary text-white rounded-lg hover:bg-competitor-primary-dark">提交</button>
        </div>
      </div>
    </div>

    <!-- 任务详情弹窗 -->
    <div v-if="selectedTask" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-[560px]">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-bold text-competitor-text">任务详情 · {{ selectedTask.name }}</h3>
          <button @click="selectedTask = null" class="text-xl leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
        <div class="space-y-3 text-sm">
          <div class="grid grid-cols-2 gap-2">
            <div><span class="text-xs text-competitor-text-2">类型</span><div>{{ selectedTask.typeLabel }}</div></div>
            <div><span class="text-xs text-competitor-text-2">状态</span><div>{{ selectedTask.statusLabel }}</div></div>
            <div><span class="text-xs text-competitor-text-2">工作流</span><div>{{ selectedTask.workflow || '—' }}</div></div>
            <div><span class="text-xs text-competitor-text-2">节点</span><div>{{ selectedTask.node || '—' }}</div></div>
            <div><span class="text-xs text-competitor-text-2">资源锁</span><div>🔒 {{ selectedTask.resource }}</div></div>
            <div><span class="text-xs text-competitor-text-2">模式</span><div>{{ selectedTask.modeLabel }}</div></div>
            <div><span class="text-xs text-competitor-text-2">进度</span><div>{{ selectedTask.progress }}%</div></div>
            <div><span class="text-xs text-competitor-text-2">ETA</span><div>{{ selectedTask.eta }}</div></div>
          </div>
          <!-- 结果回写（PRD §6.4） -->
          <div>
            <div class="text-xs font-medium text-competitor-text-2 mb-1">结果回写变量池</div>
            <div class="text-xs text-competitor-text font-mono bg-competitor-main border border-competitor-border rounded p-2">
              {{ selectedTask.result_ref }}
            </div>
          </div>
          <!-- 超时配置 -->
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div><span class="text-competitor-text-2">超时阈值</span> <span class="font-mono">{{ selectedTask.timeout_sec }}s</span></div>
            <div><span class="text-competitor-text-2">轮询间隔</span> <span class="font-mono">{{ selectedTask.poll_interval || '—' }}s</span></div>
          </div>
          <!-- 任务审计日志 -->
          <div>
            <div class="text-xs font-medium text-competitor-text-2 mb-1">任务审计日志</div>
            <div class="space-y-1 max-h-40 overflow-y-auto">
              <div v-for="(log, i) in (selectedTask.auditLog || [])" :key="i" class="text-xs flex gap-2">
                <span class="text-competitor-text-2 shrink-0 font-mono">{{ log.ts }}</span>
                <span class="text-competitor-text">[{{ log.action }}] {{ log.detail }}（{{ log.by }}）</span>
              </div>
              <div v-if="!selectedTask.auditLog?.length" class="text-xs text-competitor-text-2">暂无审计记录</div>
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
import axios from 'axios'

const tasks = ref([])
const search = ref('')
const filterType = ref('')
const filterWorkflow = ref('')
const filterResource = ref('')
const createModal = ref(false)
const selectedTask = ref(null)
const toast = ref('')

const newTask = ref({ name: '', type: '异步测试任务', workflow: '', node: '', resource: '', poll_interval: 15, timeout_sec: 3600, mode: 'poll' })

const taskTypes = [
  { value: '异步测试任务', label: '异步测试任务' },
  { value: '回归任务', label: '回归任务' },
  { value: '探索任务', label: '探索任务' },
  { value: '外部智能体任务', label: '外部智能体任务' },
  { value: '数据生成任务', label: '数据生成任务' },
]

const boardColumns = [
  { key: 'running', label: '运行中', dotClass: 'w-2 h-2 rounded-full bg-competitor-primary', progressClass: 'bg-competitor-primary' },
  { key: 'success', label: '已完成', dotClass: 'w-2 h-2 rounded-full bg-competitor-success', progressClass: 'bg-competitor-success' },
  { key: 'failed', label: '失败', dotClass: 'w-2 h-2 rounded-full bg-competitor-danger', progressClass: 'bg-competitor-danger' },
  { key: 'timeout', label: '超时', dotClass: 'w-2 h-2 rounded-full bg-competitor-warning', progressClass: 'bg-competitor-warning' },
]

const allTasks = computed(() => tasks.value)

const workflowOptions = computed(() => {
  const set = new Set()
  tasks.value.forEach(t => { if (t.workflow) set.add(t.workflow) })
  return [...set].sort()
})

const resourceOptions = computed(() => {
  const set = new Set()
  tasks.value.forEach(t => { if (t.resource) set.add(t.resource) })
  return [...set].sort()
})

const filteredTasks = computed(() => {
  return tasks.value.filter(t => {
    if (search.value && !t.name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterType.value && t.type !== filterType.value) return false
    if (filterWorkflow.value && t.workflow !== filterWorkflow.value) return false
    if (filterResource.value && t.resource !== filterResource.value) return false
    return true
  })
})

function tasksByStatus(status) {
  return filteredTasks.value.filter(t => t.status === status)
}

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

function progressClass(status) {
  return { running: 'bg-competitor-primary', success: 'bg-competitor-success', failed: 'bg-competitor-danger', timeout: 'bg-competitor-warning' }[status] || 'bg-competitor-primary'
}

async function refresh() {
  try {
    const res = await axios.get('/api/tasks')
    tasks.value = res.data || []
  } catch (e) {
    console.error('加载异步任务失败', e)
  }
}

function openCreate() {
  newTask.value = { name: '', type: '异步测试任务', workflow: '', node: '', resource: '', poll_interval: 15, timeout_sec: 3600, mode: 'poll' }
  createModal.value = true
}

async function confirmCreate() {
  try {
    await axios.post('/api/tasks', {
      name: newTask.value.name.trim(),
      type: newTask.value.type,
      workflow: newTask.value.workflow,
      node: newTask.value.node,
      resource: newTask.value.resource,
      poll_interval: newTask.value.poll_interval,
      timeout_sec: newTask.value.timeout_sec,
      mode: newTask.value.mode,
    })
    await refresh()
    createModal.value = false
    showToast('异步任务已提交')
  } catch (e) {
    showToast('提交失败：' + (e.message || e))
  }
}

function viewTask(task) {
  selectedTask.value = task
}

async function cancelTask(task) {
  try {
    await axios.post(`/api/tasks/${task.id}/cancel`, { detail: '手动取消任务，资源锁已释放' })
    await refresh()
    showToast('任务已取消')
  } catch (e) {
    showToast('取消失败：' + (e.message || e))
  }
}

async function pollTask(task) {
  try {
    const res = await axios.post(`/api/tasks/${task.id}/poll`)
    await refresh()
    if (res.data.changed) {
      showToast(res.data.task.status === 'success' ? '任务完成，结果已写回变量池' : `轮询推进，进度 ${res.data.task.progress}%`)
    } else {
      showToast('任务已结束，进度未变化')
    }
  } catch (e) {
    showToast('轮询失败：' + (e.message || e))
  }
}

async function timeoutTask(task) {
  try {
    await axios.post(`/api/tasks/${task.id}/timeout`, { detail: `超过最大执行时长（${task.timeout_sec}s），按策略终止，转人工处理` })
    await refresh()
    showToast('任务已标记为超时')
  } catch (e) {
    showToast('超时标记失败：' + (e.message || e))
  }
}

onMounted(refresh)
</script>
