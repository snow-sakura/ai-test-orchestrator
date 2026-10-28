<template>
  <div class="space-y-5">
    <!-- 页头（竞品对齐：page-header / page-title / header-actions） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">审计证据账本</h1>
        <p class="text-xs text-competitor-text-2 mt-0.5">
          共 {{ filteredEvents.length }} 条证据 · 哈希链不可篡改 · 支持按类型 / 工作流 / 节点 / 证据 ID 查询（PRD §6.6）
        </p>
      </div>
      <div class="header-actions">
        <button
          @click="verifyChain"
          class="px-3 py-2 border border-competitor-border text-competitor-text text-sm rounded-lg hover:bg-competitor-main transition-colors"
        >校验哈希链</button>
        <button
          @click="openExport"
          class="px-3 py-2 border border-competitor-border text-competitor-text text-sm rounded-lg hover:bg-competitor-main transition-colors"
        >导出账本</button>
        <button
          @click="openAppend"
          class="px-4 py-2 bg-competitor-primary text-white text-sm rounded-lg hover:bg-competitor-primary-dark transition-colors shadow-sm"
        >＋ 追加证据</button>
      </div>
    </div>

    <!-- 哈希链状态条 -->
    <div class="card-container p-3 flex items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <span
          v-if="chainState !== null"
          class="text-xs font-bold px-2.5 py-1 rounded-full"
          :class="chainState.verified ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
        >
          {{ chainState.verified ? '✓ 哈希链完整' : '✗ 哈希链已断裂' }}
        </span>
        <span class="text-xs text-competitor-text-2">
          共 {{ chainState ? chainState.total : '—' }} 条 · 末端哈希
          <code class="font-mono text-[10px] bg-competitor-main px-1.5 py-0.5 rounded">{{ (chainState?.lastHash || '').slice(0, 16) }}…</code>
        </span>
      </div>
      <span class="text-xs text-competitor-text-2">任意条目被篡改后，链校验立即失败</span>
    </div>

    <!-- 筛选栏 -->
    <div class="card-container">
      <div class="filter-bar">
        <input
          v-model="search"
          placeholder="搜索证据 ID / 详情..."
          class="w-56 p-2 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        />
        <select
          v-model="filterType"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部类型</option>
          <option v-for="t in eventTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <select
          v-model="filterWorkflow"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部工作流</option>
          <option v-for="w in workflowOptions" :key="w" :value="w">{{ w }}</option>
        </select>
        <select
          v-model="filterNode"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部节点</option>
          <option v-for="n in nodeOptions" :key="n" :value="n">{{ n }}</option>
        </select>
        <span v-if="search || filterType || filterWorkflow || filterNode" class="text-xs text-competitor-text-2">
          已筛选 {{ filteredEvents.length }} 条
        </span>
      </div>

      <!-- 证据列表 -->
      <div class="space-y-2 max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
        <div
          v-for="(ev, idx) in filteredEvents"
          :key="ev.id"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-mono text-[11px] text-competitor-text-2">[{{ idx + 1 }}]</span>
                <h3 class="font-bold text-competitor-text text-sm">{{ ev.typeLabel || ev.type }}</h3>
                <span class="text-[10px] px-2 py-0.5 rounded-full" :class="typeClass(ev.type)">{{ ev.type }}</span>
              </div>
              <div class="text-[11px] text-competitor-text-2 mt-1">
                {{ ev.workflow }} · {{ ev.node }} · 操作方：{{ ev.actor }}
              </div>
              <div class="text-xs text-competitor-text mt-1">{{ ev.detail }}</div>
              <div class="flex flex-wrap gap-3 mt-2 text-[10px] text-competitor-text-2">
                <span>🕓 {{ ev.ts }}</span>
                <span>🔗 证据引用：<code class="font-mono">{{ ev.refId }}</code></span>
                <span>🧾 ID：<code class="font-mono">{{ ev.id }}</code></span>
              </div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-[10px] text-competitor-text-2 mb-0.5">哈希</div>
              <code class="text-[10px] font-mono bg-competitor-main border border-competitor-border rounded px-1.5 py-0.5 text-competitor-text">
                {{ ev.hash ? ev.hash.slice(0, 12) + '…' : '—' }}
              </code>
            </div>
          </div>
        </div>
        <div v-if="filteredEvents.length === 0" class="card-container p-10 text-center text-competitor-text-2 text-sm">
          暂无匹配的证据条目
        </div>
      </div>
    </div>

    <!-- 追加证据弹窗 -->
    <div v-if="appendModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-[520px] space-y-4">
        <h3 class="font-bold text-competitor-text">追加证据条目</h3>
        <label class="block text-xs font-medium text-competitor-text-2 mb-1">事件类型</label>
        <select v-model="newEvent.type" class="w-full p-2 text-sm border border-competitor-border rounded outline-none">
          <option v-for="t in eventTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="block text-xs font-medium text-competitor-text-2 mb-1">工作流</label>
            <input v-model="newEvent.workflow" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" placeholder="工作流名称" />
          </div>
          <div>
            <label class="block text-xs font-medium text-competitor-text-2 mb-1">节点</label>
            <input v-model="newEvent.node" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" placeholder="节点名称" />
          </div>
        </div>
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">操作方</label>
        <input v-model="newEvent.actor" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" placeholder="平台 / 模型 / 人工" />
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">详情</label>
        <textarea v-model="newEvent.detail" rows="2" class="w-full p-2 text-sm border border-competitor-border rounded outline-none"></textarea>
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">证据引用（refId）</label>
        <input v-model="newEvent.refId" class="w-full p-2 text-sm border border-competitor-border rounded outline-none font-mono" placeholder="trace:xxx / gate:xxx / defect:xxx" />
        <div class="flex justify-end gap-2">
          <button @click="appendModal = false" class="px-3 py-1.5 text-sm border border-competitor-border rounded-lg hover:bg-competitor-main">取消</button>
          <button @click="confirmAppend" class="px-4 py-1.5 text-sm bg-competitor-primary text-white rounded-lg hover:bg-competitor-primary-dark">追加</button>
        </div>
      </div>
    </div>

    <!-- 导出弹窗 -->
    <div v-if="exportModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-[560px]">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-bold text-competitor-text">导出审计账本（合规审计）</h3>
          <button @click="exportModal = false" class="text-xl leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
        <div v-if="exportPayload">
          <div class="flex items-center gap-2 mb-3">
            <span
              class="text-xs font-bold px-2.5 py-1 rounded-full"
              :class="exportPayload.verified ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >{{ exportPayload.verified ? '哈希链校验通过' : '哈希链已断裂' }}</span>
            <span class="text-xs text-competitor-text-2">共 {{ exportPayload.total }} 条 · 导出时间 {{ exportPayload.exportedAt }}</span>
          </div>
          <pre class="text-[10px] font-mono bg-competitor-main border border-competitor-border rounded p-3 max-h-64 overflow-auto whitespace-pre-wrap">{{ exportJson }}</pre>
          <div class="flex justify-end gap-2 mt-3">
            <button @click="downloadExport" class="px-4 py-1.5 text-sm bg-competitor-primary text-white rounded-lg hover:bg-competitor-primary-dark">下载 JSON</button>
          </div>
        </div>
        <div v-else class="text-sm text-competitor-text-2 py-6 text-center">正在导出…</div>
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

const events = ref([])
const search = ref('')
const filterType = ref('')
const filterWorkflow = ref('')
const filterNode = ref('')
const appendModal = ref(false)
const exportModal = ref(false)
const exportPayload = ref(null)
const exportJson = ref('')
const chainState = ref(null)
const toast = ref('')

const newEvent = ref({ type: '工具调用', workflow: '', node: '', actor: '', detail: '', refId: '' })

const eventTypes = [
  { value: '工具调用', label: '工具调用' },
  { value: '白名单拒绝', label: '白名单拒绝' },
  { value: '质量门禁裁决', label: '质量门禁裁决' },
  { value: '缺陷归档', label: '缺陷归档' },
  { value: '人工审批', label: '人工审批' },
  { value: '升级处理', label: '升级处理' },
]

const workflowOptions = computed(() => {
  const set = new Set()
  events.value.forEach(e => { if (e.workflow) set.add(e.workflow) })
  return [...set].sort()
})

const nodeOptions = computed(() => {
  const set = new Set()
  events.value.forEach(e => { if (e.node) set.add(e.node) })
  return [...set].sort()
})

const filteredEvents = computed(() => {
  return events.value.filter(e => {
    if (filterType.value && e.type !== filterType.value) return false
    if (filterWorkflow.value && e.workflow !== filterWorkflow.value) return false
    if (filterNode.value && e.node !== filterNode.value) return false
    if (search.value) {
      const q = search.value.toLowerCase()
      if (!e.id.toLowerCase().includes(q) && !(e.detail || '').toLowerCase().includes(q) && !(e.refId || '').toLowerCase().includes(q)) return false
    }
    return true
  })
})

function typeClass(type) {
  return {
    '工具调用': 'bg-blue-100 text-blue-700',
    '白名单拒绝': 'bg-red-100 text-red-700',
    '质量门禁裁决': 'bg-purple-100 text-purple-700',
    '缺陷归档': 'bg-amber-100 text-amber-700',
    '人工审批': 'bg-green-100 text-green-700',
    '升级处理': 'bg-gray-100 text-gray-600',
  }[type] || 'bg-gray-100 text-gray-600'
}

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2200)
}

async function refresh() {
  try {
    const [evRes, chainRes] = await Promise.all([
      axios.get('/api/audit'),
      axios.get('/api/audit/verify'),
    ])
    events.value = (evRes.data || []).map(e => ({ ...e, typeLabel: e.type }))
    chainState.value = chainRes.data
  } catch (e) {
    console.error('加载审计账本失败', e)
  }
}

async function verifyChain() {
  try {
    const res = await axios.get('/api/audit/verify')
    chainState.value = res.data
    await refresh()
    showToast(res.data.verified ? '哈希链校验通过' : `哈希链在第 ${res.data.brokenAt + 1} 条断裂`)
  } catch (e) {
    showToast('校验失败：' + (e.message || e))
  }
}

function openAppend() {
  newEvent.value = { type: '工具调用', workflow: '', node: '', actor: '', detail: '', refId: '' }
  appendModal.value = true
}

async function confirmAppend() {
  try {
    await axios.post('/api/audit', {
      type: newEvent.value.type,
      workflow: newEvent.value.workflow.trim() || '手动追加',
      node: newEvent.value.node.trim() || '—',
      actor: newEvent.value.actor.trim() || '平台',
      detail: newEvent.value.detail.trim() || '手动追加的证据条目',
      refId: newEvent.value.refId.trim() || 'manual:' + Date.now(),
    })
    await refresh()
    appendModal.value = false
    showToast('证据已追加，哈希链已更新')
  } catch (e) {
    showToast('追加失败：' + (e.message || e))
  }
}

async function openExport() {
  exportModal.value = true
  exportPayload.value = null
  try {
    const res = await axios.get('/api/audit/export')
    exportPayload.value = res.data
    exportJson.value = JSON.stringify(res.data, null, 2)
  } catch (e) {
    showToast('导出失败：' + (e.message || e))
    exportModal.value = false
  }
}

function downloadExport() {
  if (!exportPayload.value) return
  const blob = new Blob([exportJson.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-ledger-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
  showToast('账本已导出')
}

onMounted(refresh)
</script>
