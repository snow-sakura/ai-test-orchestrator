<template>
  <div class="space-y-5">
    <!-- 页头（竞品对齐：page-header / page-title / header-actions） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">认证资产库</h1>
        <p class="text-xs text-competitor-text-2 mt-0.5">
          共 {{ filteredAssets.length }} 项认证资产 · 支持检索、质量门槛判定、版本锁定、退役提醒（PRD §6.3）
        </p>
      </div>
      <div class="header-actions">
        <button
          @click="openCreate"
          class="px-4 py-2 bg-competitor-primary text-white text-sm rounded-lg hover:bg-competitor-primary-dark transition-colors shadow-sm"
        >＋ 新建资产</button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="card-container">
      <div class="filter-bar">
        <input
          v-model="search"
          placeholder="搜索资产名称..."
          class="w-56 p-2 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        />
        <select
          v-model="filterType"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部类型</option>
          <option v-for="t in assetTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <select
          v-model="filterStatus"
          class="px-2 py-1.5 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        >
          <option value="">全部状态</option>
          <option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <span v-if="search || filterType || filterStatus" class="text-xs text-competitor-text-2">
          已筛选 {{ filteredAssets.length }} 项
        </span>
      </div>

      <!-- 资产卡片网格 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 max-h-[calc(100vh-320px)] overflow-y-auto pr-1">
        <div
          v-for="asset in filteredAssets"
          :key="asset.id"
          class="polaroid-card rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h3 class="font-bold text-competitor-text truncate">{{ asset.name }}</h3>
                <span
                  class="status-tag shrink-0"
                  :class="statusClass(asset.status)"
                >{{ statusLabel(asset.status) }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-competitor-main text-competitor-text shrink-0">
                  v{{ asset.version }}
                </span>
              </div>
              <div class="text-[11px] text-competitor-text-2 mt-1">
                {{ asset.typeLabel }} · {{ asset.id }}
              </div>
              <!-- 适用范围标签 -->
              <div class="flex flex-wrap gap-1 mt-1.5">
                <span
                  v-for="s in (asset.scope || [])"
                  :key="s"
                  class="text-[10px] px-1.5 py-0.5 rounded bg-competitor-main border border-competitor-border text-competitor-text-2"
                >{{ s }}</span>
              </div>
              <!-- 质量门槛判定明细（PRD §6.3） -->
              <div class="mt-2 space-y-0.5">
                <div
                  v-for="check in (asset.qualityChecks || [])"
                  :key="check.key"
                  class="flex items-center justify-between text-[11px]"
                >
                  <span class="text-competitor-text-2">{{ check.label }}</span>
                  <span
                    :class="check.passed ? 'text-competitor-success' : 'text-competitor-danger'"
                  >
                    {{ check.value }} {{ check.passed ? '✓' : '✗'}}
                  </span>
                </div>
                <div v-if="asset.qualityGate" class="text-[10px] text-competitor-text-2 mt-0.5">
                  质量门槛：{{ asset.qualityGate }}
                </div>
              </div>
              <!-- 失效提醒（PRD §6.3 资产退役） -->
              <div
                v-if="asset.retireAlert"
                class="mt-2 text-[11px] px-2 py-1 bg-red-50 border border-red-200 text-competitor-danger rounded"
              >
                ⚠ 该资产可能已失效，需重新认证或降级为普通资产
              </div>
              <!-- 复用引用（版本锁定） -->
              <div v-if="(asset.references || []).length" class="mt-2">
                <div class="text-[10px] text-competitor-text-2 mb-0.5">复用引用（版本锁定）</div>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="ref in asset.references"
                    :key="ref"
                    class="text-[10px] px-2 py-0.5 bg-competitor-main rounded-full text-competitor-text-2"
                  >
                    {{ ref }} → v{{ asset.pinnedVersions?.[ref] || asset.version }}
                  </span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1 shrink-0 flex-col">
              <button @click="viewAsset(asset)" class="text-xs px-2 py-1 border border-competitor-border rounded hover:bg-competitor-main">查看</button>
              <button
                v-if="['pending','rejected'].includes(asset.status)"
                @click="certifyAsset(asset)"
                class="text-xs px-2 py-1 bg-competitor-primary text-white rounded hover:bg-competitor-primary-dark"
              >认证</button>
              <button
                v-if="asset.status === 'certified'"
                @click="retireAsset(asset)"
                class="text-xs px-2 py-1 border border-red-200 text-competitor-danger rounded hover:bg-red-50"
              >退役</button>
            </div>
          </div>
        </div>
        <div v-if="filteredAssets.length === 0" class="col-span-full card-container p-10 text-center text-competitor-text-2 text-sm">
          暂无匹配的认证资产
        </div>
      </div>
    </div>

    <!-- 新建资产弹窗 -->
    <div v-if="createModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-96 space-y-4">
        <h3 class="font-bold text-competitor-text">新建认证资产</h3>
        <label class="block text-xs font-medium text-competitor-text-2 mb-1">名称</label>
        <input v-model="newAsset.name" class="w-full p-2 text-sm border border-competitor-border rounded outline-none focus:ring-1 focus:ring-competitor-primary" placeholder="资产名称" />
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">类型</label>
        <select v-model="newAsset.type" class="w-full p-2 text-sm border border-competitor-border rounded outline-none">
          <option v-for="t in assetTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">版本号</label>
        <input v-model.number="newAsset.version" type="number" min="1" class="w-full p-2 text-sm border border-competitor-border rounded outline-none" />
        <div class="flex justify-end gap-2">
          <button @click="createModal = false" class="px-3 py-1.5 text-sm border border-competitor-border rounded-lg hover:bg-competitor-main">取消</button>
          <button @click="confirmCreate" class="px-4 py-1.5 text-sm bg-competitor-primary text-white rounded-lg hover:bg-competitor-primary-dark">创建</button>
        </div>
      </div>
    </div>

    <!-- 资产详情弹窗 -->
    <div v-if="selectedAsset" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-[560px]">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-bold text-competitor-text">资产详情 · {{ selectedAsset.name }}</h3>
          <button @click="selectedAsset = null" class="text-xl leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
        <div class="space-y-3 text-sm">
          <div class="grid grid-cols-2 gap-2">
            <div><span class="text-xs text-competitor-text-2">类型</span><div>{{ selectedAsset.typeLabel }}</div></div>
            <div><span class="text-xs text-competitor-text-2">状态</span><div>{{ statusLabel(selectedAsset.status) }}</div></div>
            <div><span class="text-xs text-competitor-text-2">版本</span><div>v{{ selectedAsset.version }}</div></div>
            <div><span class="text-xs text-competitor-text-2">认证时间</span><div>{{ selectedAsset.certifiedAt || '—' }}</div></div>
          </div>
          <div>
            <div class="text-xs font-medium text-competitor-text-2 mb-1">质量门槛判定明细</div>
            <div class="space-y-1">
              <div v-for="check in (selectedAsset.qualityChecks || [])" :key="check.key" class="flex items-center justify-between text-xs">
                <span class="text-competitor-text">{{ check.label }}（{{ check.threshold }}）</span>
                <span :class="check.passed ? 'text-competitor-success' : 'text-competitor-danger'">
                  {{ check.value }} {{ check.passed ? '✓' : '✗' }}
                </span>
              </div>
            </div>
          </div>
          <div>
            <div class="text-xs font-medium text-competitor-text-2 mb-1">状态变更审计日志</div>
            <div class="space-y-1 max-h-40 overflow-y-auto">
              <div v-for="(log, i) in (selectedAsset.auditLog || [])" :key="i" class="text-xs flex gap-2">
                <span class="text-competitor-text-2 shrink-0 font-mono">{{ log.ts }}</span>
                <span class="text-competitor-text">[{{ log.action }}] {{ log.detail }}（{{ log.by }}）</span>
              </div>
              <div v-if="!selectedAsset.auditLog?.length" class="text-xs text-competitor-text-2">暂无审计记录</div>
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

const assets = ref([])
const search = ref('')
const filterType = ref('')
const filterStatus = ref('')
const createModal = ref(false)
const selectedAsset = ref(null)
const toast = ref('')

const newAsset = ref({ name: '', type: '用例', version: 1 })

const assetTypes = [
  { value: '用例', label: '认证用例' },
  { value: '脚本', label: '认证自动化脚本' },
  { value: '数据模板', label: '认证测试数据模板' },
  { value: '能力包', label: '认证能力包' },
  { value: '变更驱动用例', label: '代码变更驱动的生成用例' },
]

const statusOptions = [
  { value: 'certified', label: '已认证' },
  { value: 'pending', label: '待认证' },
  { value: 'rejected', label: '未通过' },
  { value: 'retired', label: '已退役' },
]

const filteredAssets = computed(() => {
  return assets.value.filter(a => {
    if (search.value && !a.name.toLowerCase().includes(search.value.toLowerCase())) return false
    if (filterType.value && a.type !== filterType.value) return false
    if (filterStatus.value && a.status !== filterStatus.value) return false
    return true
  })
})

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

function statusClass(status) {
  return {
    certified: 'bg-green-100 text-green-700',
    pending: 'bg-amber-100 text-amber-700',
    rejected: 'bg-red-100 text-red-700',
    retired: 'bg-gray-100 text-gray-600',
  }[status] || 'bg-gray-100 text-gray-600'
}

function statusLabel(status) {
  return { certified: '已认证', pending: '待认证', rejected: '未通过', retired: '已退役' }[status] || status
}

async function refresh() {
  try {
    const res = await axios.get('/api/assets')
    assets.value = res.data || []
  } catch (e) {
    console.error('加载认证资产失败', e)
  }
}

function openCreate() {
  newAsset.value = { name: '', type: '用例', version: 1 }
  createModal.value = true
}

async function confirmCreate() {
  try {
    await axios.post('/api/assets', {
      name: newAsset.value.name.trim(),
      type: newAsset.value.type,
      version: newAsset.value.version || 1,
      scope: ['新建'],
    })
    await refresh()
    createModal.value = false
    showToast('资产已创建')
  } catch (e) {
    showToast('创建失败：' + (e.message || e))
  }
}

async function certifyAsset(asset) {
  try {
    const res = await axios.post(`/api/assets/${asset.id}/certify`)
    const status = res.data.asset?.qualityGate === '通过' ? 'certified' : 'rejected'
    await refresh()
    showToast(status === 'certified' ? '认证通过，已升级为认证资产' : '未通过质量门槛，认证被拒绝')
  } catch (e) {
    showToast('认证失败：' + (e.message || e))
  }
}

async function retireAsset(asset) {
  try {
    await axios.post(`/api/assets/${asset.id}/retire`, { reason: '被测系统发生重大变更，资产可能失效' })
    await refresh()
    showToast('资产已退役')
  } catch (e) {
    showToast('退役失败：' + (e.message || e))
  }
}

function viewAsset(asset) {
  selectedAsset.value = asset
}

onMounted(refresh)
</script>
