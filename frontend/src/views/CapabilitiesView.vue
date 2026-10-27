<template>
  <div class="space-y-4">
    <!-- 页头（竞品对齐：page-header / page-title） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">开放能力控制台</h1>
        <p class="text-xs text-polaroid-warm-500 mt-0.5">
          {{ filteredCaps.length }} 项可调用能力 · 鉴权授权 · 危险操作审批 · 调用日志（PRD §6.1）
        </p>
      </div>
      <button
        @click="openCreate"
        class="px-4 py-2 bg-polaroid-warm-500 text-white text-sm rounded-lg hover:bg-polaroid-warm-600 transition-colors shadow-sm"
      >＋ 登记能力</button>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-2 flex-wrap">
      <button
        v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        class="px-3 py-1.5 text-sm rounded-lg transition-colors"
        :class="activeTab === tab.key ? 'bg-polaroid-warm-500 text-white' : 'bg-white border border-polaroid-warm-200 text-polaroid-warm-600 hover:bg-polaroid-warm-50'"
      >{{ tab.label }}</button>
    </div>

    <!-- ① 能力暴露清单 -->
    <div v-if="activeTab === 'list'">
      <!-- 筛选栏 -->
      <div class="flex items-center gap-2 flex-wrap mb-3">
        <select
          v-model="filterKind"
          class="px-2 py-1.5 text-sm border border-polaroid-warm-200 rounded-lg outline-none focus:ring-1 focus:ring-polaroid-warm-400 bg-white"
        >
          <option value="">全部类型</option>
          <option v-for="k in capKinds" :key="k" :value="k">{{ k }}</option>
        </select>
        <select
          v-model="filterStatus"
          class="px-2 py-1.5 text-sm border border-polaroid-warm-200 rounded-lg outline-none focus:ring-1 focus:ring-polaroid-warm-400 bg-white"
        >
          <option value="">全部状态</option>
          <option v-for="s in capStatuses" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>
      <!-- 能力卡片网格 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div
          v-for="cap in filteredCaps" :key="cap.id"
          class="polaroid-card rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h3 class="font-bold text-polaroid-warm-800 text-sm truncate">{{ cap.name }}</h3>
                <span class="text-[10px] px-2 py-0.5 rounded-full shrink-0" :class="kindClass(cap.kind)">{{ cap.kind }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full shrink-0" :class="statusClass(cap.status)">{{ cap.statusLabel }}</span>
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                来源：{{ cap.source }} · 协议：{{ cap.protocol }} · 鉴权：{{ cap.auth }}
              </div>
              <!-- 危险操作标记（PRD §6.1 危险操作审批） -->
              <div v-if="(cap.dangerousOps || []).length" class="flex flex-wrap gap-1 mt-1.5">
                <span
                  v-for="op in cap.dangerousOps" :key="op"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-red-50 border border-red-200 text-red-600"
                >⚠ {{ op }}</span>
              </div>
              <p class="text-[11px] text-polaroid-warm-500 mt-2">{{ cap.desc }}</p>
              <div class="flex flex-wrap gap-3 mt-2 text-[10px] text-polaroid-warm-500">
                <span>30天调用 {{ cap.callCount30d }}</span>
                <span v-if="cap.lastCalled">最近调用 {{ cap.lastCalled }}</span>
              </div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-[10px] text-polaroid-warm-500 mb-0.5">能力 ID</div>
              <code class="text-[10px] font-mono bg-polaroid-warm-50 border border-polaroid-warm-200 rounded px-1.5 py-0.5 text-polaroid-warm-700">{{ cap.id }}</code>
            </div>
          </div>
        </div>
        <div v-if="filteredCaps.length === 0" class="col-span-full polaroid-card rounded-lg p-10 text-center text-polaroid-warm-500 text-sm">
          暂无匹配的能力
        </div>
      </div>
    </div>

    <!-- ② 调用日志 -->
    <div v-if="activeTab === 'callLogs'">
      <div class="flex items-center gap-2 flex-wrap mb-3">
        <select
          v-model="filterLogResult"
          class="px-2 py-1.5 text-sm border border-polaroid-warm-200 rounded-lg outline-none focus:ring-1 focus:ring-polaroid-warm-400 bg-white"
        >
          <option value="">全部结果</option>
          <option value="success">成功</option>
          <option value="pending_approval">待审批</option>
          <option value="failed">失败</option>
        </select>
      </div>
      <div class="polaroid-card rounded-lg p-4">
        <h4 class="text-sm font-bold text-polaroid-warm-800 mb-2">外部调用日志（与内部运行共享同一审计账本）</h4>
        <div class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead>
              <tr class="text-left text-polaroid-warm-500 border-b border-polaroid-warm-200">
                <th class="py-2 pr-3">时间</th>
                <th class="py-2 pr-3">能力</th>
                <th class="py-2 pr-3">调用方</th>
                <th class="py-2 pr-3">结果</th>
                <th class="py-2 pr-3">耗时</th>
                <th class="py-2 pr-3">审计引用</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in filteredCallLogs" :key="l.id" class="border-b border-polaroid-warm-100">
                <td class="py-2 pr-3 text-polaroid-warm-500 font-mono">{{ l.ts }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-700">{{ l.capability }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-600">{{ l.caller }}</td>
                <td class="py-2 pr-3">
                  <span :class="resultClass(l.result)">{{ resultLabel(l.result) }}</span>
                </td>
                <td class="py-2 pr-3 text-polaroid-warm-600 font-mono">{{ l.duration }}</td>
                <td class="py-2 pr-3 font-mono text-polaroid-warm-500">{{ l.auditRef }}</td>
              </tr>
              <tr v-if="filteredCallLogs.length === 0"><td colspan="6" class="py-4 text-center text-polaroid-warm-500">暂无调用日志</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ③ 审批记录 -->
    <div v-if="activeTab === 'approvals'">
      <div class="space-y-3">
        <div
          v-for="a in approvals" :key="a.id"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h4 class="text-xs font-bold text-polaroid-warm-800">{{ a.capability }}</h4>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">操作：{{ a.op }}</span>
                <span :class="a.status === '已放行' ? 'text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700' : 'text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700'">{{ a.status }}</span>
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                {{ a.ts }} · 审批方：{{ a.by || '—' }}
              </div>
            </div>
            <button
              v-if="a.status === '待审批'"
              @click="approve(a)"
              class="text-xs px-2 py-1 bg-polaroid-warm-500 text-white rounded hover:bg-polaroid-warm-600 shrink-0"
            >放行</button>
          </div>
        </div>
        <div v-if="approvals.length === 0" class="polaroid-card rounded-lg p-8 text-center text-polaroid-warm-500 text-sm">暂无审批记录</div>
      </div>
    </div>

    <!-- ④ 接入配置 -->
    <div v-if="activeTab === 'connects'">
      <div class="space-y-3">
        <div
          v-for="c in connects" :key="c.id"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h4 class="text-xs font-bold text-polaroid-warm-800">{{ c.caller }}</h4>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">{{ c.role }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full" :class="c.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'">{{ c.status === 'active' ? '已接入' : '已停用' }}</span>
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                密钥：<code class="font-mono">{{ c.keyMasked }}</code> · 创建于 {{ c.created }}
              </div>
              <div class="flex flex-wrap gap-1 mt-1.5">
                <span v-for="s in c.scopes" :key="s" class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">{{ s }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="connects.length === 0" class="polaroid-card rounded-lg p-8 text-center text-polaroid-warm-500 text-sm">暂无接入配置</div>
      </div>
    </div>

    <!-- 登记能力弹窗 -->
    <div v-if="createModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="bg-white rounded-xl shadow-xl w-96 p-5 space-y-4">
        <h3 class="font-bold text-polaroid-warm-800">登记对外能力</h3>
        <label class="block text-xs font-medium opacity-60 mb-1">能力名称</label>
        <input v-model="newCap.name" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="能力名称" />
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">类型</label>
        <select v-model="newCap.kind" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
          <option v-for="k in capKinds" :key="k" :value="k">{{ k }}</option>
        </select>
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">来源（工作流 / 节点 ID）</label>
        <input v-model="newCap.source" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none font-mono" placeholder="wf_xxx / n_xxx" />
        <div class="flex justify-end gap-2">
          <button @click="createModal = false" class="px-3 py-1.5 text-sm border border-polaroid-warm-300 rounded-lg hover:bg-polaroid-warm-100">取消</button>
          <button @click="confirmCreate" class="px-4 py-1.5 text-sm bg-polaroid-warm-500 text-white rounded-lg hover:bg-polaroid-warm-600">登记</button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="toast" class="fixed bottom-6 right-6 z-50 px-4 py-2 bg-polaroid-warm-900 text-white text-sm rounded-lg shadow-lg">
      {{ toast }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const caps = ref([])
const callLogs = ref([])
const approvals = ref([])
const connects = ref([])

const activeTab = ref('list')
const tabs = [
  { key: 'list', label: '能力暴露清单' },
  { key: 'callLogs', label: '调用日志' },
  { key: 'approvals', label: '审批记录' },
  { key: 'connects', label: '接入配置' },
]

const filterKind = ref('')
const filterStatus = ref('')
const filterLogResult = ref('')
const createModal = ref(false)
const toast = ref('')
const newCap = ref({ name: '', kind: '工作流', source: '' })

const capKinds = ['工作流', '节点', '工具', '规则']
const capStatuses = [
  { value: 'active', label: '已上线' },
  { value: 'pending_approval', label: '待审批' },
  { value: 'disabled', label: '已下线' },
]

const filteredCaps = computed(() => {
  return caps.value.filter(c => {
    if (filterKind.value && c.kind !== filterKind.value) return false
    if (filterStatus.value && c.status !== filterStatus.value) return false
    return true
  })
})

const filteredCallLogs = computed(() => {
  if (!filterLogResult.value) return callLogs.value
  return callLogs.value.filter(l => l.result === filterLogResult.value)
})

function kindClass(kind) {
  return { 工作流: 'bg-blue-100 text-blue-700', 节点: 'bg-green-100 text-green-700', 工具: 'bg-purple-100 text-purple-700', 规则: 'bg-gray-100 text-gray-600' }[kind] || 'bg-gray-100 text-gray-600'
}

function statusClass(status) {
  return { active: 'bg-green-100 text-green-700', pending_approval: 'bg-amber-100 text-amber-700', disabled: 'bg-gray-100 text-gray-600' }[status] || 'bg-gray-100 text-gray-600'
}

function resultClass(result) {
  return { success: 'text-green-600', pending_approval: 'text-amber-600', failed: 'text-red-500' }[result] || 'text-polaroid-warm-600'
}

function resultLabel(result) {
  return { success: '成功', pending_approval: '待审批', failed: '失败' }[result] || result
}

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2200)
}

async function refresh() {
  try {
    const [capRes, logRes, appRes, connRes] = await Promise.all([
      axios.get('/api/capabilities'),
      axios.get('/api/capabilities/call-logs'),
      axios.get('/api/capabilities/approvals'),
      axios.get('/api/capabilities/connects'),
    ])
    caps.value = capRes.data || []
    callLogs.value = logRes.data || []
    approvals.value = appRes.data || []
    connects.value = connRes.data || []
  } catch (e) {
    console.error('加载开放能力失败', e)
  }
}

function openCreate() {
  newCap.value = { name: '', kind: '工作流', source: '' }
  createModal.value = true
}

async function confirmCreate() {
  try {
    await axios.post('/api/capabilities', {
      name: newCap.value.name.trim(),
      kind: newCap.value.kind,
      source: newCap.value.source.trim(),
    })
    await refresh()
    createModal.value = false
    showToast('能力已登记')
  } catch (e) {
    showToast('登记失败：' + (e.message || e))
  }
}

async function approve(a) {
  try {
    await axios.post(`/api/capabilities/approvals/${a.id}/approve`, { by: '测试负责人' })
    await refresh()
    showToast('审批已放行')
  } catch (e) {
    showToast('审批失败：' + (e.message || e))
  }
}

onMounted(refresh)
</script>
