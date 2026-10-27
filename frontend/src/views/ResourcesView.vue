<template>
  <div class="space-y-4">
    <!-- 页头（竞品对齐：page-header / page-title） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">资源与锁管理</h1>
        <p class="text-xs text-polaroid-warm-500 mt-0.5">
          资源池 · 锁模式 · TTL 倒计时 · 冲突策略（PRD §6.2）
        </p>
      </div>
      <button
        @click="openCreatePool"
        class="px-4 py-2 bg-polaroid-warm-500 text-white text-sm rounded-lg hover:bg-polaroid-warm-600 transition-colors shadow-sm"
      >＋ 登记资源池</button>
    </div>

    <!-- 汇总条 -->
    <div class="grid grid-cols-2 md:grid-cols-6 gap-3">
      <div class="polaroid-card rounded-lg p-3">
        <div class="text-[11px] text-polaroid-warm-500">资源池</div>
        <div class="text-xl font-bold text-polaroid-warm-800 mt-0.5">{{ summary.poolCount }}</div>
      </div>
      <div class="polaroid-card rounded-lg p-3">
        <div class="text-[11px] text-polaroid-warm-500">资源成员</div>
        <div class="text-xl font-bold text-polaroid-warm-800 mt-0.5">{{ summary.totalMembers }}</div>
      </div>
      <div class="polaroid-card rounded-lg p-3">
        <div class="text-[11px] text-polaroid-warm-500">锁定中成员</div>
        <div class="text-xl font-bold text-polaroid-warm-700 mt-0.5">{{ summary.lockedCount }}</div>
      </div>
      <div class="polaroid-card rounded-lg p-3">
        <div class="text-[11px] text-polaroid-warm-500">活动锁</div>
        <div class="text-xl font-bold text-polaroid-warm-700 mt-0.5">{{ summary.activeLocks }}</div>
      </div>
      <div class="polaroid-card rounded-lg p-3">
        <div class="text-[11px] text-polaroid-warm-500">排队中</div>
        <div class="text-xl font-bold text-amber-600 mt-0.5">{{ summary.queueCount }}</div>
      </div>
      <div class="polaroid-card rounded-lg p-3">
        <div class="text-[11px] text-polaroid-warm-500">锁事件</div>
        <div class="text-xl font-bold text-polaroid-warm-700 mt-0.5">{{ summary.eventCount }}</div>
      </div>
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

    <!-- ① 资源池 -->
    <div v-if="activeTab === 'pools'">
      <div class="flex items-center gap-2 flex-wrap mb-3">
        <select
          v-model="filterPoolType"
          class="px-2 py-1.5 text-sm border border-polaroid-warm-200 rounded-lg outline-none focus:ring-1 focus:ring-polaroid-warm-400 bg-white"
        >
          <option value="">全部类型</option>
          <option v-for="t in resTypes" :key="t" :value="t">{{ t }}</option>
        </select>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div
          v-for="pool in filteredPools" :key="pool.id"
          class="polaroid-card rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h3 class="font-bold text-polaroid-warm-800 text-sm">{{ pool.typeLabel }} · {{ pool.name }}</h3>
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">共 {{ pool.total }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">锁定 {{ pool.locked }}</span>
                <span class="text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700">空闲 {{ pool.free }}</span>
              </div>
            </div>
          </div>
          <!-- 成员列表 -->
          <div class="mt-3 space-y-2">
            <div
              v-for="m in pool.members" :key="m.id"
              class="polaroid-card rounded-lg p-3"
            >
              <div class="flex items-center justify-between gap-2">
                <div class="min-w-0 flex-1 flex items-center gap-2">
                  <span class="text-xs font-bold text-polaroid-warm-800 truncate">{{ m.label }}</span>
                  <span class="text-[10px] px-2 py-0.5 rounded-full shrink-0" :class="m.status === 'locked' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'">
                    {{ m.status === 'locked' ? '锁定中' : '空闲' }}
                  </span>
                </div>
                <div class="text-right text-[10px] text-polaroid-warm-500 shrink-0">
                  <div v-if="m.status === 'locked'">持有：{{ m.holder }}</div>
                  <div v-if="m.status === 'locked' && m.ttl">TTL {{ m.ttl }}s</div>
                  <div v-else>无占用</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="filteredPools.length === 0" class="col-span-full polaroid-card rounded-lg p-10 text-center text-polaroid-warm-500 text-sm">暂无匹配的资源池</div>
      </div>
    </div>

    <!-- ② 资源锁 -->
    <div v-if="activeTab === 'locks'">
      <div class="flex items-center gap-2 flex-wrap mb-3">
        <select
          v-model="filterLockStatus"
          class="px-2 py-1.5 text-sm border border-polaroid-warm-200 rounded-lg outline-none focus:ring-1 focus:ring-polaroid-warm-400 bg-white"
        >
          <option value="">全部状态</option>
          <option value="locked">锁定中</option>
          <option value="free">已释放</option>
        </select>
        <button
          @click="openAcquire"
          class="ml-auto px-3 py-1.5 text-xs bg-polaroid-warm-500 text-white rounded-lg hover:bg-polaroid-warm-600"
        >＋ 获取锁</button>
      </div>
      <div class="space-y-3">
        <div
          v-for="lock in filteredLocks" :key="lock.id"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h4 class="text-xs font-bold text-polaroid-warm-800">资源：{{ lock.resourceId }}</h4>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">{{ lock.mode }}</span>
                <span :class="lock.status === 'locked' ? 'text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700' : 'text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700'">
                  {{ lock.status === 'locked' ? '锁定中' : '已释放' }}
                </span>
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                持有方：{{ lock.holder }} · 获取于 {{ lock.acquiredAt }} · TTL {{ lock.ttl }}s{{ lock.autoRelease ? '（自动释放）' : '' }}
              </div>
              <div v-if="lock.status === 'free' && lock.releasedAt" class="text-[11px] text-polaroid-warm-500 mt-0.5">
                释放于 {{ lock.releasedAt }} · 释放方：{{ lock.releasedBy }}
              </div>
            </div>
            <button
              v-if="lock.status === 'locked'"
              @click="releaseLock(lock)"
              class="text-xs px-2 py-1 border border-polaroid-warm-300 text-polaroid-warm-600 rounded hover:bg-polaroid-warm-50 shrink-0"
            >释放</button>
          </div>
        </div>
        <div v-if="filteredLocks.length === 0" class="polaroid-card rounded-lg p-8 text-center text-polaroid-warm-500 text-sm">暂无资源锁</div>
      </div>
    </div>

    <!-- ③ 锁事件 -->
    <div v-if="activeTab === 'events'">
      <div class="flex items-center gap-2 flex-wrap mb-3">
        <select
          v-model="filterEventAction"
          class="px-2 py-1.5 text-sm border border-polaroid-warm-200 rounded-lg outline-none focus:ring-1 focus:ring-polaroid-warm-400 bg-white"
        >
          <option value="">全部动作</option>
          <option v-for="a in ['获取', '释放', '持有']" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>
      <div class="polaroid-card rounded-lg p-4">
        <h4 class="text-sm font-bold text-polaroid-warm-800 mb-2">锁事件时间线（持有 / 释放 / 冲突挂起，可追溯）</h4>
        <div class="overflow-x-auto">
          <table class="w-full text-xs">
            <thead>
              <tr class="text-left text-polaroid-warm-500 border-b border-polaroid-warm-200">
                <th class="py-2 pr-3">时间</th>
                <th class="py-2 pr-3">资源</th>
                <th class="py-2 pr-3">动作</th>
                <th class="py-2 pr-3">执行方</th>
                <th class="py-2 pr-3">详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in filteredEvents" :key="e.id" class="border-b border-polaroid-warm-100">
                <td class="py-2 pr-3 text-polaroid-warm-500 font-mono">{{ e.ts }}</td>
                <td class="py-2 pr-3 font-mono text-polaroid-warm-700">{{ e.resourceId }}</td>
                <td class="py-2 pr-3">
                  <span :class="e.action === '释放' ? 'text-green-600' : e.action === '持有' ? 'text-amber-600' : 'text-polaroid-warm-600'">{{ e.action }}</span>
                </td>
                <td class="py-2 pr-3 text-polaroid-warm-600">{{ e.actor }}</td>
                <td class="py-2 pr-3 text-polaroid-warm-500">{{ e.detail }}</td>
              </tr>
              <tr v-if="filteredEvents.length === 0"><td colspan="5" class="py-4 text-center text-polaroid-warm-500">暂无锁事件</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ④ 冲突队列 -->
    <div v-if="activeTab === 'queue'">
      <div class="space-y-3">
        <div
          v-for="q in queueItems" :key="q.id"
          class="polaroid-card rounded-lg p-4"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <h4 class="text-xs font-bold text-polaroid-warm-800">资源：{{ q.resourceId }}</h4>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-polaroid-warm-50 border border-polaroid-warm-200 text-polaroid-warm-600">策略：{{ q.policy }}</span>
              </div>
              <div class="text-[11px] text-polaroid-warm-500 mt-1">
                请求方：{{ q.requester }} · 挂起于 {{ q.ts }} · 已等待 {{ q.waitSec }}s
              </div>
            </div>
          </div>
        </div>
        <div v-if="queueItems.length === 0" class="polaroid-card rounded-lg p-8 text-center text-polaroid-warm-500 text-sm">无排队中的资源冲突</div>
      </div>
    </div>

    <!-- 登记资源池弹窗 -->
    <div v-if="poolModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="bg-white rounded-xl shadow-xl w-96 p-5 space-y-4">
        <h3 class="font-bold text-polaroid-warm-800">登记资源池</h3>
        <label class="block text-xs font-medium opacity-60 mb-1">资源类型</label>
        <select v-model="newPool.type" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
          <option v-for="t in resTypes" :key="t" :value="t">{{ t }}</option>
        </select>
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">资源池名称</label>
        <input v-model="newPool.name" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="资源池名称" />
        <div class="flex justify-end gap-2">
          <button @click="poolModal = false" class="px-3 py-1.5 text-sm border border-polaroid-warm-300 rounded-lg hover:bg-polaroid-warm-100">取消</button>
          <button @click="confirmPool" class="px-4 py-1.5 text-sm bg-polaroid-warm-500 text-white rounded-lg hover:bg-polaroid-warm-600">登记</button>
        </div>
      </div>
    </div>

    <!-- 获取锁弹窗 -->
    <div v-if="lockModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="bg-white rounded-xl shadow-xl w-96 p-5 space-y-4">
        <h3 class="font-bold text-polaroid-warm-800">获取资源锁</h3>
        <label class="block text-xs font-medium opacity-60 mb-1">资源 ID</label>
        <input v-model="newLock.resourceId" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none font-mono" placeholder="dev_a / env_staging / slot_1 ..." />
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">持有方（工作流 · 节点）</label>
        <input v-model="newLock.holder" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="工作流名 · 节点名" />
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium opacity-60 mb-1">锁模式</label>
            <select v-model="newLock.mode" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              <option>独占锁</option>
              <option>共享锁</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium opacity-60 mb-1">TTL（秒）</label>
            <input v-model.number="newLock.ttl" type="number" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" />
          </div>
        </div>
        <label class="block text-xs font-medium opacity-60 mt-3 mb-1">冲突策略</label>
        <select v-model="newLock.policy" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
          <option>排队等待</option>
          <option>直接失败</option>
          <option>超时释放</option>
        </select>
        <div class="flex justify-end gap-2">
          <button @click="lockModal = false" class="px-3 py-1.5 text-sm border border-polaroid-warm-300 rounded-lg hover:bg-polaroid-warm-100">取消</button>
          <button @click="confirmLock" class="px-4 py-1.5 text-sm bg-polaroid-warm-500 text-white rounded-lg hover:bg-polaroid-warm-600">获取</button>
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

const pools = ref([])
const locks = ref([])
const events = ref([])
const queueItems = ref([])
const summary = ref({ poolCount: 0, totalMembers: 0, lockedCount: 0, activeLocks: 0, queueCount: 0, eventCount: 0 })

const resTypes = ['设备', '环境', '凭据', '并发槽位', '数据源']

const activeTab = ref('pools')
const tabs = [
  { key: 'pools', label: '资源池' },
  { key: 'locks', label: '资源锁' },
  { key: 'events', label: '锁事件' },
  { key: 'queue', label: '冲突队列' },
]

const filterPoolType = ref('')
const filterLockStatus = ref('')
const filterEventAction = ref('')

const poolModal = ref(false)
const lockModal = ref(false)
const toast = ref('')
const newPool = ref({ type: '设备', name: '' })
const newLock = ref({ resourceId: '', holder: '', mode: '独占锁', ttl: 600, policy: '排队等待' })

const filteredPools = computed(() => {
  if (!filterPoolType.value) return pools.value
  return pools.value.filter(p => p.type === filterPoolType.value)
})

const filteredLocks = computed(() => {
  if (!filterLockStatus.value) return locks.value
  return locks.value.filter(l => l.status === filterLockStatus.value)
})

const filteredEvents = computed(() => {
  if (!filterEventAction.value) return events.value
  return events.value.filter(e => e.action === filterEventAction.value)
})

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2200)
}

async function refresh() {
  try {
    const [poolRes, lockRes, eventRes, queueRes, sumRes] = await Promise.all([
      axios.get('/api/resources/pools'),
      axios.get('/api/resources/locks'),
      axios.get('/api/resources/events'),
      axios.get('/api/resources/queue'),
      axios.get('/api/resources/summary'),
    ])
    pools.value = poolRes.data || []
    locks.value = lockRes.data || []
    events.value = eventRes.data || []
    queueItems.value = queueRes.data || []
    summary.value = sumRes.data || {}
  } catch (e) {
    console.error('加载资源与锁失败', e)
  }
}

function openCreatePool() {
  newPool.value = { type: '设备', name: '' }
  poolModal.value = true
}

async function confirmPool() {
  try {
    await axios.post('/api/resources/pools', {
      type: newPool.value.type,
      name: newPool.value.name.trim(),
      members: [],
    })
    await refresh()
    poolModal.value = false
    showToast('资源池已登记')
  } catch (e) {
    showToast('登记失败：' + (e.message || e))
  }
}

function openAcquire() {
  newLock.value = { resourceId: '', holder: '', mode: '独占锁', ttl: 600, policy: '排队等待' }
  lockModal.value = true
}

async function confirmLock() {
  try {
    await axios.post('/api/resources/locks', {
      resourceId: newLock.value.resourceId.trim(),
      holder: newLock.value.holder.trim(),
      mode: newLock.value.mode,
      ttl: newLock.value.ttl || 600,
      policy: newLock.value.policy,
    })
    await refresh()
    lockModal.value = false
    showToast('锁已获取')
  } catch (e) {
    showToast('获取失败：' + (e.message || e))
  }
}

async function releaseLock(lock) {
  try {
    await axios.post(`/api/resources/locks/${lock.id}/release`, { by: '平台管理员' })
    await refresh()
    showToast('锁已释放')
  } catch (e) {
    showToast('释放失败：' + (e.message || e))
  }
}

onMounted(refresh)
</script>
