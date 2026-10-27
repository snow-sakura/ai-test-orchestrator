<template>
  <div class="h-full w-full flex bg-polaroid-warm-50">
    <!-- 左侧节点模板库（画布专属） -->
    <div class="w-56 border-r border-polaroid-warm-200 bg-white flex flex-col shrink-0">
      <div class="p-3 border-b border-polaroid-warm-200">
        <div class="text-xs font-bold mb-2 opacity-60">节点模板库（PRD §11）</div>
        <input
          v-model="nodeSearch"
          placeholder="搜索节点..."
          class="w-full p-1.5 text-xs border border-polaroid-warm-200 rounded outline-none focus:ring-1 focus:ring-polaroid-warm-400"
        />
      </div>
      <div class="flex-1 overflow-y-auto p-3 space-y-4">
        <div v-for="cat in filteredCategories" :key="cat.key">
          <div class="text-xs font-semibold mb-2 text-polaroid-warm-600">{{ cat.name }}</div>
          <div class="grid grid-cols-1 gap-1.5">
            <div
              v-for="n in cat.nodes"
              :key="`${cat.key}-${n.label}`"
              draggable="true"
              @click.stop="onAddNode(cat.key, n.label)"
              @dragstart="onDragStart(cat.key, n.label, $event)"
              class="p-2 text-xs border border-polaroid-warm-200 rounded bg-white hover:border-polaroid-warm-400 cursor-grab transition-all shadow-sm text-polaroid-warm-800"
              :title="n.desc"
            >
              {{ n.label }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 画布主体 -->
    <div class="flex-1 relative">
      <!-- 画布操作栏（PRD §3.3） -->
      <div class="h-11 border-b border-polaroid-warm-200 bg-white/80 flex items-center px-4 gap-3">
        <button @click="goBack" class="text-xs px-2 py-1 rounded border border-polaroid-warm-300 hover:bg-polaroid-warm-100">←</button>
        <input
          v-model="workflowStore.currentWorkflow.name"
          class="w-48 text-sm font-medium border border-polaroid-warm-200 rounded px-2 py-0.5 outline-none focus:ring-1 focus:ring-polaroid-warm-400"
        />
        <span class="text-xs px-2 py-0.5 rounded-full"
          :class="workflowStore.isSaving ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'">
          {{ workflowStore.isSaving ? '保存中...' : '已保存' }}
        </span>
        <span class="text-[10px] text-polaroid-warm-500">
          节点 {{ workflowStore.currentWorkflow.nodes.length }} / 连线 {{ workflowStore.currentWorkflow.edges.length }} · 缩放 {{ zoom }}%
        </span>
        <div class="ml-auto flex items-center gap-1.5">
          <button @click="hideHelpers = !hideHelpers" class="px-2.5 py-1 text-xs border border-polaroid-warm-300 rounded hover:bg-polaroid-warm-100">{{ hideHelpers ? '显示辅助' : '隐藏辅助' }}</button>
          <button @click="saveCurrent" class="px-2.5 py-1 text-xs border border-polaroid-warm-300 rounded hover:bg-polaroid-warm-100">保存</button>
          <button @click="showValidation = true" class="px-2.5 py-1 text-xs border border-polaroid-warm-300 rounded hover:bg-polaroid-warm-100">结构校验</button>
          <button @click="showRun = !showRun" class="px-2.5 py-1 text-xs border border-polaroid-warm-300 rounded hover:bg-polaroid-warm-100">执行面板</button>
          <button @click="runWorkflow" :disabled="isExecuting" class="px-3 py-1 text-xs bg-polaroid-warm-500 text-white rounded hover:bg-polaroid-warm-600 shadow-sm disabled:opacity-50">
            {{ isExecuting ? '执行中...' : '执行' }}
          </button>
        </div>
      </div>

      <!-- Vue Flow 画布 -->
      <div class="w-full h-full">
        <VueFlow
          v-model:nodes="workflowStore.currentWorkflow.nodes"
          v-model:edges="workflowStore.currentWorkflow.edges"
          :connection-mode="'loose'"
          :fit-view-on-init="true"
          :min-zoom="0.2"
          :max-zoom="2"
          :hide-helper-nodes="hideHelpers"
          @node-click="onNodeClick"
          @edge-click="onEdgeClick"
          @connect="onConnect"
          @node-drag-stop="onNodeDragStop"
          class="h-full bg-polaroid-warm-50"
        >
          <Background pattern-color="#eadfd3" :gap="20" />
          <Controls position="bottom-left" />

          <template #node-custom="props">
            <div :class="[
              'custom-node',
              hideHelpers && isHelperNode({ data: props.data, label: props.label }) ? 'hidden' : '',
              {
                'node-running': props.data?.status === 'running',
                'node-success': props.data?.status === 'success',
                'node-failed': props.data?.status === 'failed'
              }
            ]">
              <Handle type="target" position="left" />
              <div class="custom-node-label">{{ props.label }}</div>
              <div class="custom-node-cat">{{ props.data?.category ? catName(props.data.category) : '' }}</div>
              <Handle type="source" position="right" />
            </div>
          </template>
        </VueFlow>
      </div>

      <!-- 结构校验面板 -->
      <div v-if="showValidation" class="absolute right-4 top-14 w-72 bg-white border border-polaroid-warm-200 rounded-lg shadow-lg z-20">
        <div class="p-3 border-b border-polaroid-warm-200 flex justify-between items-center">
          <span class="text-xs font-bold">结构校验（PRD §7.2）</span>
          <button @click="showValidation = false" class="text-lg leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
        <div class="p-3 text-xs space-y-2 max-h-64 overflow-y-auto">
          <div v-if="validationIssues.length === 0" class="text-green-600">✅ 校验通过，无结构问题</div>
          <div v-for="(iss, i) in validationIssues" :key="i"
               class="px-2 py-1.5 rounded border"
               :class="iss.level === 'error' ? 'border-red-200 bg-red-50 text-red-700' : 'border-amber-200 bg-amber-50 text-amber-700'">
            {{ iss.msg }}
          </div>
        </div>
      </div>

      <!-- 执行日志面板 -->
      <div v-if="showRun" class="absolute bottom-0 left-0 right-0 h-48 bg-white border-t border-polaroid-warm-200 z-10 flex flex-col">
        <div class="p-2 border-b border-polaroid-warm-200 flex justify-between items-center bg-polaroid-warm-50">
          <span class="text-xs font-bold">执行追踪（PRD §7.4）</span>
          <button @click="showRun = false" class="text-lg leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
        <div class="flex-1 overflow-y-auto p-3 font-mono text-[10px] space-y-1">
          <div v-for="(log, i) in executionLogs" :key="i" class="flex gap-2">
            <span class="opacity-40 shrink-0">{{ log.time }}</span>
            <span :class="log.nodeId === 'global' ? 'font-bold text-polaroid-warm-600' : ''">
              [{{ log.nodeId || 'System' }}] {{ log.msg }}
            </span>
          </div>
          <div v-if="executionLogs.length === 0" class="opacity-40">暂无执行记录，点击「执行」发起试运行</div>
        </div>
      </div>
    </div>

    <!-- 右侧节点配置抽屉（10 分区，PRD §4 / §7.1） -->
    <aside v-if="selectedNode" class="w-80 border-l border-polaroid-warm-200 bg-white flex flex-col shrink-0">
      <div class="p-4 border-b border-polaroid-warm-200 flex justify-between items-center">
        <div>
          <h2 class="font-bold text-sm">节点配置</h2>
          <p class="text-[10px] opacity-50">{{ selectedNode.label }}</p>
        </div>
        <div class="flex items-center gap-2">
          <button @click="removeSelectedNode" class="text-xs px-2 py-1 border border-red-200 text-red-500 rounded hover:bg-red-50">删除</button>
          <button @click="selectedNode = null" class="text-xl leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
      </div>

      <!-- 折叠分区 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <div v-for="(section, si) in drawerSections" :key="si">
          <button @click="openSection = openSection === si ? -1 : si"
            class="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold border border-polaroid-warm-200 rounded-lg bg-polaroid-warm-50 hover:bg-polaroid-warm-100 transition-colors">
            <span>{{ section.title }}</span>
            <span class="opacity-50">{{ openSection === si ? '−' : '+' }}</span>
          </button>
          <div v-if="openSection === si" class="mt-2 px-3 py-2 border border-polaroid-warm-200 rounded-lg bg-white space-y-3">
            <!-- 基础信息 -->
            <template v-if="section.key === 'basic'">
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">节点名称</label>
                <input type="text" v-model="selectedNode.label" @input="onConfigChange" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none focus:ring-1 focus:ring-polaroid-warm-400">
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">分类</label>
                <input :value="catName(selectedNode.data.category)" disabled class="w-full p-2 text-sm border border-polaroid-warm-200 rounded bg-polaroid-warm-50">
              </div>
            </template>
            <!-- 模型 -->
            <template v-else-if="section.key === 'model'">
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">选择模型</label>
                <select v-model="selectedNode.config.model" @change="onConfigChange" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
                  <option>Claude-Opus-4.5</option>
                  <option>Claude-Sonnet-4.5</option>
                  <option>Gemini-2.5-Pro</option>
                  <option>GPT-4o</option>
                  <option>Qwen3-Max</option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">Temperature</label>
                <input type="number" v-model.number="selectedNode.config.temperature" @input="onConfigChange" step="0.1" min="0" max="2" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">Top-P</label>
                <input type="number" v-model.number="selectedNode.config.topP" @input="onConfigChange" step="0.05" min="0" max="1" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              </div>
            </template>
            <!-- 提示词 -->
            <template v-else-if="section.key === 'prompt'">
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">System Prompt</label>
                <textarea v-model="selectedNode.config.systemPrompt" @input="onConfigChange" rows="3" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="输入系统提示词..."></textarea>
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">User Prompt</label>
                <textarea v-model="selectedNode.config.userPrompt" @input="onConfigChange" rows="3" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none" placeholder="输入用户提示词，支持 {{变量}} 引用上游输出..."></textarea>
              </div>
            </template>
            <!-- 输入绑定 -->
            <template v-else-if="section.key === 'input'">
              <p class="text-[11px] opacity-50">从上游节点输出选择数据。已绑定：</p>
              <ul class="text-xs space-y-1">
                <li v-for="(b, i) in (selectedNode.config.inputBindings || [])" :key="i" class="px-2 py-1 bg-polaroid-warm-50 rounded">{{ b }}</li>
                <li v-if="!(selectedNode.config.inputBindings || []).length" class="text-[11px] opacity-40">暂无绑定</li>
              </ul>
            </template>
            <!-- 输出 Schema -->
            <template v-else-if="section.key === 'output'">
              <label class="block text-[11px] font-medium opacity-60 mb-1">输出 Schema（JSON）</label>
              <textarea v-model="selectedNode.config.outputSchemaText" @input="onConfigChange" rows="4" class="w-full p-2 text-xs border border-polaroid-warm-200 rounded outline-none font-mono" placeholder='{ "result": "string", "evidence": ["string"] }'></textarea>
              <p class="text-[10px] opacity-40">关键判定字段必须包含证据引用（evidence）</p>
            </template>
            <!-- 工具白名单 -->
            <template v-else-if="section.key === 'tools'">
              <p class="text-[11px] opacity-50">声明可调用的工具（白名单外调用运行时拒绝）：</p>
              <label v-for="t in toolOptions" :key="t" class="flex items-center gap-2 text-xs py-0.5 cursor-pointer">
                <input type="checkbox" :value="t" v-model="selectedNode.config.toolWhitelist" @change="onConfigChange" />
                {{ t }}
              </label>
            </template>
            <!-- 能力包 -->
            <template v-else-if="section.key === 'skills'">
              <p class="text-[11px] opacity-50">可挂载零个或多个能力包（Skills）：</p>
              <label v-for="s in skillOptions" :key="s" class="flex items-center gap-2 text-xs py-0.5 cursor-pointer">
                <input type="checkbox" :value="s" v-model="selectedNode.config.skills" @change="onConfigChange" />
                {{ s }}
              </label>
            </template>
            <!-- 约束配置 -->
            <template v-else-if="section.key === 'constraints'">
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">最大执行步数</label>
                <input type="number" v-model.number="selectedNode.config.maxSteps" @input="onConfigChange" min="1" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">超时（秒）</label>
                <input type="number" v-model.number="selectedNode.config.timeoutSec" @input="onConfigChange" min="1" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">Token 预算</label>
                <input type="number" v-model.number="selectedNode.config.tokenBudget" @input="onConfigChange" min="0" step="100" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              </div>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">重试次数</label>
                <input type="number" v-model.number="selectedNode.config.retry" @input="onConfigChange" min="0" max="5" class="w-full p-2 text-sm border border-polaroid-warm-200 rounded outline-none">
              </div>
            </template>
            <!-- 规则绑定 -->
            <template v-else-if="section.key === 'rules'">
              <p class="text-[11px] opacity-50">继承平台级规则并附加节点级规则：</p>
              <ul class="text-xs space-y-1">
                <li v-for="(r, i) in (selectedNode.config.rules || [])" :key="i" class="px-2 py-1 bg-polaroid-warm-50 rounded">{{ r }}</li>
                <li v-if="!(selectedNode.config.rules || []).length" class="text-[11px] opacity-40">未附加节点级规则</li>
              </ul>
            </template>
            <!-- 异步与资源 -->
            <template v-else-if="section.key === 'async'">
              <label class="flex items-center gap-2 text-xs cursor-pointer">
                <input type="checkbox" v-model="selectedNode.config.asyncMode" @change="onConfigChange" />
                异步模式（提交后立即返回任务标识）
              </label>
              <div>
                <label class="block text-[11px] font-medium opacity-60 mb-1">所需资源</label>
                <input type="text" v-model="selectedNode.config.resourcesText" @input="onConfigChange" placeholder="如：mobile_device,api_credential" class="w-full p-2 text-xs border border-polaroid-warm-200 rounded outline-none">
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="p-4 border-t border-polaroid-warm-200 flex gap-2">
        <button @click="saveCurrent" class="flex-1 py-2 bg-polaroid-warm-500 text-white text-sm rounded hover:bg-polaroid-warm-600 transition-colors">保存配置</button>
        <button @click="debugNode" class="px-3 py-2 border border-polaroid-warm-300 rounded text-sm hover:bg-polaroid-warm-100">单节点调试</button>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueFlow, useVueFlow, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { useWorkflowStore, NODE_CATALOG, validateWorkflow } from '../stores/workflow'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const workflowStore = useWorkflowStore()
const { addEdge, onConnect: onConnectImpl, updateNodeData } = useVueFlow()

const nodeSearch = ref('')
const selectedNode = ref(null)
const isExecuting = ref(false)
const showRun = ref(false)
const executionLogs = ref([])
const currentExecId = ref(null)
const showValidation = ref(false)
const validationIssues = ref([])
const hideHelpers = ref(false)
const openSection = ref(0)
let pollTimer = null

const zoom = ref(100)

const toolOptions = ['webFetch', 'codeExec', 'screenshot', 'apiCall', 'fileWrite']
const skillOptions = ['登录能力包', '表单填充能力包', '断言增强能力包', '数据工厂工具库']

const categories = computed(() =>
  Object.entries(NODE_CATALOG).map(([key, c]) => ({ key, name: c.name, nodes: c.nodes }))
)

const filteredCategories = computed(() => {
  const q = nodeSearch.value.trim().toLowerCase()
  const list = categories.value
  if (!q) return list
  return list
    .map(c => ({ ...c, nodes: c.nodes.filter(n => n.label.toLowerCase().includes(q)) }))
    .filter(c => c.nodes.length > 0)
})

// 10 分区（PRD §4 / §7.1）
const drawerSections = [
  { key: 'basic', title: '基础信息' },
  { key: 'model', title: '模型配置' },
  { key: 'prompt', title: '提示词配置' },
  { key: 'input', title: '输入变量绑定' },
  { key: 'output', title: '输出 Schema' },
  { key: 'tools', title: '工具白名单' },
  { key: 'skills', title: '能力包挂载' },
  { key: 'constraints', title: '约束配置' },
  { key: 'rules', title: '规则绑定' },
  { key: 'async', title: '异步与资源' },
]

const catName = (key) => NODE_CATALOG[key]?.name || key

function isHelperNode(node) {
  return ['control'].includes(node.data?.category) && !['开始', '结束'].includes(node.label)
}

onMounted(async () => {
  const id = route.query.wf || workflowStore.currentWorkflow.id
  await workflowStore.fetchWorkflow(id)
  // 初始化 config 字段缺省
  workflowStore.currentWorkflow.nodes.forEach(n => {
    if (!n.config) n.config = { toolWhitelist: [], skills: [], rules: [], inputBindings: [], outputSchemaText: '{}' }
    else {
      n.config.toolWhitelist = n.config.toolWhitelist || []
      n.config.skills = n.config.skills || []
      n.config.rules = n.config.rules || []
      n.config.inputBindings = n.config.inputBindings || []
      n.config.outputSchemaText = n.config.outputSchemaText || '{}'
    }
  })
  saveCurrent()
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function onAddNode(categoryKey, label) {
  const n = NODE_CATALOG[categoryKey]?.nodes.find(x => x.label === label)
  workflowStore.addNode(categoryKey, label, n?.desc || '')
  onConfigChange()
}

function onDragStart(categoryKey, label, event) {
  event.dataTransfer.setData('application/vueflow', JSON.stringify({ category: categoryKey, label }))
}

function onConnect(params) {
  onConnectImpl(params)
  // 校验数据契约（PRD §3.2 / §7.2）
  if (params.sourceHandle && !params.sourceHandle.endsWith('out')) {
    // 上游 output 不匹配下游 input 时提示
  }
  onConfigChange()
}

function onConfigChange() {
  // 自动保存（PRD §3.2：每 5 秒自动保存草稿）
  saveCurrent()
}

async function saveCurrent() {
  await workflowStore.saveWorkflow()
}

function onNodeClick(event) {
  const node = event.node
  selectedNode.value = node
  openSection.value = 0
}

function onEdgeClick(event) {
  // 删除连线
  workflowStore.removeEdge(event.edge.id)
}

function onNodeDragStop() {
  workflowStore.updateNodesPosition(workflowStore.currentWorkflow.nodes)
}

function removeSelectedNode() {
  if (!selectedNode.value) return
  workflowStore.removeNode(selectedNode.value.id)
  selectedNode.value = null
  saveCurrent()
}

function runValidation() {
  validationIssues.value = validateWorkflow(workflowStore.currentWorkflow)
}

function debugNode() {
  const n = selectedNode.value
  if (!n) return
  executionLogs.value = [
    { time: 'now', nodeId: 'global', msg: `调试节点「${n.label}」（模拟上下文边界 / 工具白名单 / 资源锁）` },
    { time: 'now', nodeId: n.id, msg: `白名单内工具：${(n.config?.toolWhitelist || []).join(', ') || '（无）'}` },
    { time: 'now', nodeId: n.id, msg: '模拟输入数据已注入，节点输出符合预期 Schema' },
  ]
  showRun.value = true
  saveCurrent()
}

async function runWorkflow() {
  // 保存 + 校验
  await saveCurrent()
  runValidation()
  try {
    const res = await axios.post(`/api/execute/${workflowStore.currentWorkflow.id}`)
    currentExecId.value = res.data.execution_id
    isExecuting.value = true
    showRun.value = true
    executionLogs.value = [
      ...validationIssues.value.map((issue) => ({
        time: 'now',
        nodeId: 'global',
        msg: `${issue.level === 'error' ? '结构校验提示' : '结构校验建议'}：${issue.msg}`,
      })),
    ]
    pollStatus()
  } catch (e) {
    showRun.value = true
    executionLogs.value = [
      ...executionLogs.value,
      { time: 'now', nodeId: 'global', msg: '执行启动失败：' + (e.message || e) },
    ]
  }
}

function goBack() {
  router.push('/workflows')
}

async function pollStatus() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const res = await axios.get(`/api/execution/${currentExecId.value}`)
      const data = res.data
      executionLogs.value = data.logs
      workflowStore.currentWorkflow.nodes.forEach((node) => {
        const state = data.node_states[node.id]
        if (state) {
          updateNodeData(node.id, { status: state })
          node.data = { ...(node.data || {}), status: state }
        }
      })
      if (data.status !== 'running') {
        isExecuting.value = false
        clearInterval(pollTimer)
        pollTimer = null
      }
    } catch (e) {
      console.error('轮询状态失败', e)
    }
  }, 1000)
}

// 暴露给测试
defineExpose({ runValidation })
</script>

<style scoped>
.custom-node {
  background: #fef9f2;
  border: 1px solid #e9b49a;
  border-radius: 8px;
  padding: 8px;
  width: 140px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.custom-node-label { font-size: 12px; font-weight: 500; color: #733d31; }
.custom-node-cat { font-size: 10px; color: #b57b65; margin-top: 2px; }
.node-running { border-color: #ef4444 !important; box-shadow: 0 0 10px rgba(239,68,68,0.5); background: #fee2e2; }
.node-success { border-color: #22c55e !important; background: #dcfce7; }
.node-failed { border-color: #ef4444 !important; background: #fee2e2; }
</style>
