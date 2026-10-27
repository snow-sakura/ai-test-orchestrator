<template>
  <div class="p-6 space-y-4">
    <!-- 顶部操作栏 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-bold text-polaroid-warm-800">模型与额度</h2>
        <p class="text-xs text-polaroid-warm-600 mt-0.5">
          {{ registry.length }} 个可用模型 · 三层配置（全站 / 个人 / 角色） · 额度授予与成本计量（PRD §6.5）
        </p>
      </div>
      <button
        @click="openGrant"
        class="px-4 py-2 bg-polaroid-warm-500 text-white text-sm rounded-lg hover:bg-polaroid-warm-600 transition-colors shadow-sm"
      >＋ 额度授予</button>
    </div>

    <!-- Tab 切换 -->
    <div class="flex gap-2">
      <button
        v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        class="px-3 py-1.5 text-sm rounded-lg transition-colors"
        :class="activeTab === tab.key ? 'bg-polaroid-warm-500 text-white' : 'bg-white border border-polaroid-warm-200 text-polaroid-warm-600 hover:bg-polaroid-warm-50'"
      >{{ tab.label }}</button>
    </div>

    <!-- ① 模型注册表 -->
    <div v-if="activeTab === 'registry'">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div
          v-for="m in registry" :key="m.id"
          class="polaroid-card rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <h3 class="font-bold text-polaroid-warm-800 text-sm">{{ m.name }}</h3>
              <div class="text-[11px] text-polaroid-warm-500 mt-0.5">{{ m.vendor }} · {{ m.kind }} · 上下文 {{ m.context }}</div>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded-full shrink-0" :class="tierClass(m.tier)">{{ m.tier }}档</span>
          </div>
          <div class="flex flex-wrap gap-1 mt-2">
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">日限 {{ m.dailyLimit }}</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">¥{{ m.pricePerMIn }}/M 入</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">¥{{ m.pricePerMOut }}/M 出</span>
          </div>
          <p class="text-[11px] text-polaroid-warm-500 mt-2">{{ m.desc }}</p>
        </div>
      </div>
    </div>

    <!-- ② 三层配置 -->
    <div v-if="activeTab === 'configs'">
      <div class="space-y-3">
        <div
          v-for="c in configs" :key="c.level + c.owner"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-[10px] px-2 py-0.5 rounded-full" :class="levelClass(c.level)">{{ c.level }}级</span>
                <h3 class="font-bold text-polaroid-warm-800 text-sm">{{ c.owner || '全站默认' }}</h3>
                <span v-if="c.connected" class="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700">已连接</span>
                <span v-else class="text-[10px] px-2 py-0.5 rounded-full bg-red-100 text-red-700">未连接</span>
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                文本模型：{{ c.textModelName }} · 视觉模型：{{ c.visionModelName || '—' }}
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                参数：temperature {{ c.params?.temperature ?? '—' }} · maxTokens {{ c.params?.maxTokens ?? '—' }}
              </div>
              <div class="text-[11px] text-polaroid-warm-400 mt-1">
                🔑 {{ c.keyMasked }}（{{ c.keyMaskedSource }}）
              </div>
            </div>
            <div class="flex items-center gap-1 shrink-0 flex-col">
              <button @click="testConfig(c)" class="text-xs px-2 py-1 bg-polaroid-warm-500 text-white rounded hover:bg-polaroid-warm-600">连接测试</button>
              <button @click="openEditConfig(c)" class="text-xs px-2 py-1 border border-polaroid-warm-300 rounded hover:bg-polaroid-warm-100">编辑</button>
            </div>
          </div>
        </div>
        <div v-if="configs.length === 0" class="polaroid-card rounded-lg p-8 text-center text-polaroid-warm-500 text-sm">暂无配置</div>
      </div>
    </div>

    <!-- ③ 额度管理 -->
    <div v-if="activeTab === 'quota'">
      <div class="space-y-4">
        <!-- 当日额度卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            v-for="q in quotas" :key="q.model"
            class="polaroid-card rounded-lg p-4"
          >
            <div class="flex items-center justify-between">
              <h4 class="text-xs font-bold text-polaroid-warm-800">{{ q.modelName }}</h4>
              <button
                @click="renewQuota(q)"
                class="text-[10px] px-2 py-0.5 bg-polaroid-warm-500 text-white rounded hover:bg-polaroid-warm-600"
              >＋ 叠加额度</button>
            </div>
            <div class="mt-2">
              <div class="h-2 bg-polaroid-warm-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :class="q.available === 0 ? 'bg-red-500' : 'bg-green-500'"
                  :style="{ width: q.usedRatio + '%' }"
                ></div>
              </div>
            </div>
            <div class="flex items-center justify-between mt-2 text-[11px] text-polaroid-warm-500">
              <span>已用 {{ q.usedToday }} / 基础 {{ q.dailyLimit }} + 叠加 {{ q.extraToday }}</span>
              <span :class="q.available === 0 ? 'text-red-500 font-medium' : 'text-polaroid-warm-600'">可用 {{ q.available }}</span>
            </div>
          </div>
        </div>

        <!-- 授予记录 -->
        <div class="polaroid-card rounded-lg p-4">
          <h4 class="text-sm font-bold text-polaroid-warm-800 mb-2">额度授予记录（按账号 · 可撤销）</h4>
          <div class="space-y-2">
            <div v-for="g in grants" :key="g.id" class="flex items-center justify-between text-xs gap-2">
              <span class="text-polaroid-warm-600">{{ g.account }} · {{ g.modelName }}</span>
              <span class="text-polaroid-warm-500">{{ g.date }} 叠加 +{{ g.extraQuota }}</span>
              <span v-if="g.revoked" class="px-1.5 py-0.5 bg-red-100 text-red-600 rounded text-[10px]">已撤销</span>
              <button
                v-if="!g.revoked"
                @click="revokeGrant(g)"
                class="text-[10px] px-2 py-0.5 border border-red-200 text-red-500 rounded hover:bg-red-50"
              >撤销</button>
            </div>
            <div v-if="grants.length === 0" class="text-xs text-polaroid-warm-500">暂无授予记录</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ④ 用量与成本 -->
    <div v-if="activeTab === 'usage'">
      <div class="polaroid-card rounded-lg p-4">
        <h4 class="text-sm font-bold text-polaroid-warm-800 mb-2">计量与成本（按工作流 / 节点 / 模型维度）</h4>
        <div class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead>
              <tr class="text-left text-polaroid-warm-500 border-b border-polaroid-warm-200">
                <th class="py-2 pr-3">模型</th>
                <th class="py-2 pr-3">工作流</th>
                <th class="py-2 pr-3">节点</th>
                <th class="py-2 pr-3">Token</th>
                <th class="py-2 pr-3">成本</th>
                <th class="py-2 pr-3">时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in usage" :key="u.id" class="border-b border-polaroid-warm-100">
                <td class="py-2 pr-3 font-medium text-polaroid-warm-800">{{ u.modelName }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-600">{{ u.workflow }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-600">{{ u.node }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-700 font-mono">{{ u.tokens }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-700 font-mono">¥{{ u.cost.toFixed(4) }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-500">{{ u.ts }}</td>
              </tr>
              <tr v-if="usage.length === 0"><td colspan="6" class="py-4 text-center text-polaroid-warm-500">暂无用量记录</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 额度授予弹窗 -->
    <div v-if="grantModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="bg-white rounded-xl shadow-xl w-96 p-5 space-y-4">
        <h3 class="font-bold text-polaroid-warm-800">额度授予</h3>
        <label class="block text-xs font-medium opacity-60 mb-1">账号</label>
        <input v-model="newGrant.account" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="测试负责人" />
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">模型</label>
        <select v-model="newGrant.model" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
          <option v-for="m in registry" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">额外使用次数</label>
        <input v-model.number="newGrant.extraQuota" type="number" min="1" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" />
        <div class="flex justify-end gap-2">
          <button @click="grantModal = false" class="px-3 py-1.5 text-sm border border-polaroid-warm-300 rounded-lg hover:bg-polaroid-warm-100">取消</button>
          <button @click="confirmGrant" class="px-4 py-1.5 text-sm bg-polaroid-warm-500 text-white rounded-lg hover:bg-polaroid-warm-600">授予</button>
        </div>
      </div>
    </div>

    <!-- 编辑配置弹窗 -->
    <div v-if="editModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="bg-white rounded-xl shadow-xl w-96 p-5 space-y-4">
        <h3 class="font-bold text-polaroid-warm-800">编辑配置 · {{ editForm.owner || '全站默认' }}</h3>
        <label class="block text-xs font-medium opacity-60 mb-1">文本模型</label>
        <select v-model="editForm.textModel" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
          <option v-for="m in registry.filter(r => r.kind !== '视觉')" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">视觉模型（可选）</label>
        <select v-model="editForm.visionModel" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
          <option value="">—</option>
          <option v-for="m in registry.filter(r => r.kind === '视觉' || r.kind === '多模态')" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
        <div class="grid grid-cols-2 gap-2 mt-3">
          <div>
            <label class="block text-xs font-medium opacity-60 mb-1">temperature</label>
            <input v-model.number="editForm.temperature" type="number" step="0.1" min="0" max="2" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" />
          </div>
          <div>
            <label class="block text-xs font-medium opacity-60 mb-1">maxTokens</label>
            <input v-model.number="editForm.maxTokens" type="number" min="1" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" />
          </div>
        </div>
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">密钥（掩码）</label>
        <input v-model="editForm.keyMasked" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="sk-••••••••" />
        <div class="flex justify-end gap-2">
          <button @click="editModal = false" class="px-3 py-1.5 text-sm border border-polaroid-warm-300 rounded-lg hover:bg-polaroid-warm-100">取消</button>
          <button @click="confirmEditConfig" class="px-4 py-1.5 text-sm bg-polaroid-warm-500 text-white rounded-lg hover:bg-polaroid-warm-600">保存</button>
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
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const registry = ref([])
const configs = ref([])
const grants = ref([])
const quotas = ref([])
const usage = ref([])

const activeTab = ref('registry')
const tabs = [
  { key: 'registry', label: '模型注册表' },
  { key: 'configs', label: '三层配置' },
  { key: 'quota', label: '额度管理' },
  { key: 'usage', label: '用量与成本' },
]

const grantModal = ref(false)
const newGrant = ref({ account: '测试负责人', model: '', extraQuota: 100 })

const editModal = ref(false)
const editForm = reactive({ configKey: '', owner: '', level: '', textModel: '', visionModel: '', temperature: 0.2, maxTokens: 4096, keyMasked: '' })

const toast = ref('')
let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

function tierClass(tier) {
  return { 高: 'bg-purple-100 text-purple-700', 中: 'bg-blue-100 text-blue-700', 低: 'bg-gray-100 text-gray-600' }[tier] || 'bg-gray-100 text-gray-600'
}

function levelClass(level) {
  return { 全站: 'bg-purple-100 text-purple-700', 个人: 'bg-blue-100 text-blue-700', 角色: 'bg-green-100 text-green-700' }[level] || 'bg-gray-100 text-gray-600'
}

async function refresh() {
  try {
    const [reg, cfg, gr, qu, us] = await Promise.all([
      axios.get('/api/models/registry'),
      axios.get('/api/models/configs'),
      axios.get('/api/models/grants', { params: { account: '测试负责人' } }),
      axios.get('/api/models/quotas', { params: { account: '测试负责人' } }),
      axios.get('/api/models/usage'),
    ])
    registry.value = reg.data || []
    configs.value = cfg.data || []
    grants.value = gr.data || []
    quotas.value = qu.data || []
    usage.value = us.data || []
    if (newGrant.value.model === '') newGrant.value.model = (reg.data || [])[0]?.id || ''
  } catch (e) {
    console.error('加载模型数据失败', e)
  }
}

async function testConfig(c) {
  const key = c.level === '全站' ? 'global' : c.level === '个人' ? `personal_${c.owner}` : `role_${c.owner}`
  try {
    const res = await axios.post(`/api/models/configs/${encodeURIComponent(key)}/test`)
    showToast(res.data.status === 'success' ? `连接测试通过：${res.data.message}` : `连接测试失败：${res.data.message}`)
    await refresh()
  } catch (e) {
    showToast('连接测试失败：' + (e.message || e))
  }
}

function openEditConfig(c) {
  editForm.configKey = c.level === '全站' ? 'global' : c.level === '个人' ? `personal_${c.owner}` : `role_${c.owner}`
  editForm.owner = c.owner || ''
  editForm.level = c.level
  editForm.textModel = c.textModel || ''
  editForm.visionModel = c.visionModel || ''
  editForm.temperature = c.params?.temperature ?? 0.2
  editForm.maxTokens = c.params?.maxTokens ?? 4096
  editForm.keyMasked = c.keyMasked || ''
  editModal.value = true
}

async function confirmEditConfig() {
  try {
    await axios.post('/api/models/configs', {
      level: editForm.level,
      owner: editForm.owner,
      textModel: editForm.textModel,
      visionModel: editForm.visionModel,
      params: { temperature: editForm.temperature, maxTokens: editForm.maxTokens },
      keyMasked: editForm.keyMasked,
    })
    await refresh()
    editModal.value = false
    showToast('配置已保存')
  } catch (e) {
    showToast('保存失败：' + (e.message || e))
  }
}

function openGrant() {
  newGrant.value = { account: '测试负责人', model: registry.value[0]?.id || '', extraQuota: 100 }
  grantModal.value = true
}

async function confirmGrant() {
  try {
    await axios.post('/api/models/grants', newGrant.value)
    await refresh()
    grantModal.value = false
    showToast('额度已授予')
  } catch (e) {
    showToast('授予失败：' + (e.message || e))
  }
}

async function revokeGrant(g) {
  try {
    await axios.post(`/api/models/grants/${g.id}/revoke`)
    await refresh()
    showToast('授予已撤销')
  } catch (e) {
    showToast('撤销失败：' + (e.message || e))
  }
}

async function renewQuota(q) {
  try {
    await axios.post('/api/models/quotas/renew', { model: q.model, extraQuota: 200 })
    await refresh()
    showToast('已叠加 200 次当日额度')
  } catch (e) {
    showToast('叠加失败：' + (e.message || e))
  }
}

onMounted(refresh)
</script>
