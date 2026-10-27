<template>
  <div class="p-6 space-y-4">
    <!-- 顶部 -->
    <div>
      <h2 class="text-lg font-bold text-polaroid-warm-800">统一配置中心</h2>
      <p class="text-xs text-polaroid-warm-600 mt-0.5">
        驱动 / 模型 / 通知 / 环境检测 / 权限控制 · 预算与熔断（PRD §6.8 / §6.9）
      </p>
    </div>

    <!-- 左侧分区导航 -->
    <div class="flex gap-4">
      <!-- 分区列表 -->
      <div class="w-44 shrink-0 space-y-1">
        <button
          v-for="s in sections" :key="s.key"
          @click="activeSection = s.key"
          class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors"
          :class="activeSection === s.key ? 'bg-polaroid-warm-500 text-white' : 'text-polaroid-warm-600 hover:bg-polaroid-warm-50'"
        >{{ s.label }}</button>
      </div>

      <!-- 分区内容 -->
      <div class="flex-1 min-w-0 space-y-3">
        <div v-if="activeSection" class="polaroid-card rounded-lg p-4">
          <h3 class="text-sm font-bold text-polaroid-warm-800">{{ sectionLabel(activeSection) }}</h3>
          <div class="space-y-3 mt-3">
            <div
              v-for="item in activeItems" :key="item.key"
              class="border border-polaroid-warm-200 rounded-lg p-3"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 flex-1">
                  <div class="text-xs font-bold text-polaroid-warm-700">{{ item.key }}</div>
                  <div class="text-[10px] text-polaroid-warm-500 mt-0.5">{{ item.desc }}</div>
                </div>
                <!-- 控件 -->
                <select
                  v-if="item.type === 'select' || item.type === 'switch'"
                  :value="item.value"
                  @change="updateItem(activeSection, item, $event.target.value)"
                  class="shrink-0 px-2 py-1 text-xs border border-polaroid-warm-300 rounded outline-none bg-white"
                >
                  <option v-for="o in item.options" :key="o" :value="o">{{ o }}</option>
                </select>
                <input
                  v-else-if="item.type === 'number' || item.type === 'text'"
                  :value="item.value"
                  @blur="updateItem(activeSection, item, $event.target.value)"
                  :type="item.type === 'number' ? 'number' : 'text'"
                  class="shrink-0 w-28 px-2 py-1 text-xs border border-polaroid-warm-300 rounded outline-none"
                />
                <span v-else class="shrink-0 text-xs text-polaroid-warm-600">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 预算与熔断 -->
    <div>
      <h3 class="text-sm font-bold text-polaroid-warm-800 mb-3">预算、熔断与并发（平台代码强制执行，不交由模型判断）</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          v-for="b in budgets" :key="b.id"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold text-polaroid-warm-800">{{ b.scope }}</span>
            <span class="text-[10px] px-2 py-0.5 rounded-full" :class="onExceedClass(b.onExceed)">{{ b.onExceed }}</span>
          </div>
          <p class="text-[11px] text-polaroid-warm-500 mt-1">{{ b.desc }}</p>
          <div class="mt-2 space-y-1 text-[11px] text-polaroid-warm-600">
            <div v-if="b.tokenBudget">Token 预算：<b class="text-polaroid-warm-800">{{ b.tokenBudget.toLocaleString() }}</b></div>
            <div v-if="b.timeBudgetSec">时间预算：<b class="text-polaroid-warm-800">{{ b.timeBudgetSec }}s</b></div>
            <div v-if="b.maxIterations">最大迭代：<b class="text-polaroid-warm-800">{{ b.maxIterations }}</b></div>
            <div v-if="b.noProgressFuse">无进展熔断：<b class="text-polaroid-warm-800">{{ b.noProgressFuse }} 次</b></div>
          </div>
          <select
            :value="b.onExceed"
            @change="updateBudget(b, $event.target.value)"
            class="mt-2 w-full px-2 py-1 text-xs border border-polaroid-warm-300 rounded outline-none bg-white"
          >
            <option v-for="p in policies" :key="p" :value="p">{{ p }}</option>
          </select>
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

const sections = ref([])
const budgets = ref([])
const policies = ref(['硬停止', '降级输出', '升级人工'])

const activeSection = ref('')
const toast = ref('')

const activeItems = computed(() => {
  if (!activeSection.value) return []
  const sec = sections.value.find(s => s.key === activeSection.value || s.label === activeSection.value)
  return sec ? (sec.items || []) : []
})

function sectionLabel(key) {
  const sec = sections.value.find(s => s.key === key || s.label === key)
  return sec ? sec.label : key
}

function onExceedClass(v) {
  return { '硬停止': 'bg-red-100 text-red-700', '降级输出': 'bg-amber-100 text-amber-700', '升级人工': 'bg-blue-100 text-blue-700' }[v] || 'bg-gray-100 text-gray-600'
}

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

async function refresh() {
  try {
    const [secRes, budRes, metaRes] = await Promise.all([
      axios.get('/api/settings'),
      axios.get('/api/settings/budgets'),
      axios.get('/api/settings/meta'),
    ])
    sections.value = secRes.data || []
    budgets.value = budRes.data || []
    if (metaRes.data?.policies) policies.value = metaRes.data.policies
    if (sections.value.length) activeSection.value = sections.value[0].key
  } catch (e) {
    console.error('加载配置中心失败', e)
  }
}

async function updateItem(section, item, value) {
  try {
    await axios.put(`/api/settings/sections/${encodeURIComponent(section)}/items/${encodeURIComponent(item.key)}`, { key: item.key, value })
    item.value = value
    item.updatedAt = '刚刚'
    showToast('配置已保存')
  } catch (e) {
    showToast('保存失败：' + (e.message || e))
  }
}

async function updateBudget(budget, onExceed) {
  try {
    await axios.put(`/api/settings/budgets/${budget.id}`, { onExceed })
    budget.onExceed = onExceed
    showToast('预算策略已更新')
  } catch (e) {
    showToast('更新失败：' + (e.message || e))
  }
}

onMounted(refresh)
</script>
