<template>
  <div class="space-y-5">
    <!-- 页头（竞品对齐：page-header / page-title / header-actions） -->
    <div class="page-header">
      <div>
        <h1 class="page-title">工作流列表</h1>
        <p class="text-xs text-competitor-text-2 mt-0.5">共 {{ filteredWorkflows.length }} 个工作流 · 支持增删改查、发布状态、范式模板</p>
      </div>
      <div class="header-actions">
        <input
          v-model="search"
          placeholder="搜索工作流..."
          class="w-56 p-2 text-sm border border-competitor-border rounded-lg outline-none focus:ring-1 focus:ring-competitor-primary bg-white"
        />
        <button
          @click="openCreate"
          class="px-4 py-2 bg-competitor-primary text-white text-sm rounded-lg hover:bg-competitor-primary-dark transition-colors shadow-sm"
        >＋ 新建工作流</button>
      </div>
    </div>

    <!-- 范式模板 -->
    <div class="card-container">
      <div class="border-b border-competitor-border pb-3">
        <h3 class="font-semibold text-sm">典型编排范式模板（PRD §8）</h3>
        <p class="text-[11px] text-competitor-text-2 mt-0.5">点击「使用」可一键生成对应工作流骨架</p>
      </div>
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 pt-4">
        <div v-for="tpl in templates" :key="tpl.id" class="border border-competitor-border rounded-lg p-3 hover:border-competitor-primary hover:shadow-sm transition-all flex flex-col gap-2">
          <div class="text-xl">{{ tpl.icon }}</div>
          <div class="text-sm font-medium text-competitor-text flex-1">{{ tpl.name }}</div>
          <button
            @click="useTemplate(tpl.id)"
            class="text-xs px-2 py-1 bg-competitor-main rounded hover:bg-competitor-border transition-colors"
          >使用</button>
        </div>
      </div>
    </div>

    <!-- 工作流卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div
        v-for="wf in filteredWorkflows"
        :key="wf.id"
        class="polaroid-card rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="font-bold text-competitor-text truncate">{{ wf.name }}</h3>
              <span
                class="status-tag shrink-0"
                :class="wf.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'"
              >{{ wf.status === 'published' ? '已发布' : '草稿' }}</span>
            </div>
            <p class="text-[11px] text-competitor-text-2 mt-1">
              节点 {{ wf.nodes?.length || 0 }} · 连线 {{ wf.edges?.length || 0 }} · {{ wf.id }}
            </p>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button @click="previewWf = wf" class="text-xs px-2 py-1 border border-competitor-border rounded hover:bg-competitor-main">预览</button>
            <button @click="editWf(wf)" class="text-xs px-2 py-1 border border-competitor-border rounded hover:bg-competitor-main">编辑</button>
            <button @click="renameWf(wf)" class="text-xs px-2 py-1 border border-competitor-border rounded hover:bg-competitor-main">重命名</button>
            <button
              @click="toggleStatus(wf)"
              class="text-xs px-2 py-1 border border-competitor-border rounded hover:bg-competitor-main"
            >{{ wf.status === 'published' ? '撤稿' : '发布' }}</button>
            <button @click="removeWf(wf)" class="text-xs px-2 py-1 border border-red-200 text-competitor-danger rounded hover:bg-red-50">删除</button>
          </div>
        </div>
      </div>
      <div v-if="filteredWorkflows.length === 0" class="col-span-full card-container p-10 text-center text-competitor-text-2 text-sm">
        暂无匹配的工作流
      </div>
    </div>

    <!-- 新建 / 重命名 弹窗 -->
    <div v-if="modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-96 space-y-4">
        <h3 class="font-bold text-competitor-text">{{ modal === 'create' ? '新建工作流' : '重命名工作流' }}</h3>
        <div v-if="modal === 'create'">
          <label class="block text-xs font-medium text-competitor-text-2 mb-1">名称</label>
          <input v-model="newName" class="w-full p-2 text-sm border border-competitor-border rounded outline-none focus:ring-1 focus:ring-competitor-primary" placeholder="我的工作流" />
          <label class="block text-xs font-medium text-competitor-text-2 mt-3 mb-1">模板（可选）</label>
          <select v-model="newTemplate" class="w-full p-2 text-sm border border-competitor-border rounded outline-none">
            <option value="">空白工作流</option>
            <option v-for="tpl in templates" :key="tpl.id" :value="tpl.id">{{ tpl.name }}</option>
          </select>
        </div>
        <div v-else>
          <label class="block text-xs font-medium text-competitor-text-2 mb-1">新名称</label>
          <input v-model="renameName" class="w-full p-2 text-sm border border-competitor-border rounded outline-none focus:ring-1 focus:ring-competitor-primary" />
        </div>
        <div class="flex justify-end gap-2">
          <button @click="closeModal" class="px-3 py-1.5 text-sm border border-competitor-border rounded-lg hover:bg-competitor-main">取消</button>
          <button @click="confirmModal" class="px-4 py-1.5 text-sm bg-competitor-primary text-white rounded-lg hover:bg-competitor-primary-dark">确定</button>
        </div>
      </div>
    </div>

    <!-- 流程预览 弹窗 -->
    <div v-if="previewWf" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div class="card-container w-[560px]">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-bold text-competitor-text">流程预览 · {{ previewWf.name }}</h3>
          <button @click="previewWf = null" class="text-xl leading-none opacity-50 hover:opacity-100">&times;</button>
        </div>
        <div class="flex items-center gap-2 overflow-x-auto py-2">
          <div v-for="(n, i) in previewWf.nodes" :key="n.id" class="flex items-center gap-2 shrink-0">
            <span class="px-3 py-1.5 text-xs bg-competitor-main border border-competitor-border rounded-full">{{ n.label }}</span>
            <span v-if="i < previewWf.nodes.length - 1" class="text-competitor-text-2">→</span>
          </div>
          <span v-if="!previewWf.nodes?.length" class="text-xs text-competitor-text-2">该工作流暂无节点</span>
        </div>
        <div class="text-[11px] text-competitor-text-2 mt-2">
          节点数 {{ previewWf.nodes?.length || 0 }} · 连线数 {{ previewWf.edges?.length || 0 }}
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
import { useWorkflowStore } from '../stores/workflow'

const store = useWorkflowStore()
const router = useRouter()

const templates = [
  { id: 'cicd', name: 'CI/CD 质量门禁', icon: '🚦' },
  { id: 'explore', name: '智能探索回归', icon: '🕵️' },
  { id: 'mobile', name: '移动端多端回归', icon: '📱' },
  { id: 'design', name: '需求到用例', icon: '🧩' },
  { id: 'external', name: '外部智能体按需', icon: '🌐' },
]

const search = ref('')
const modal = ref(null) // 'create' | 'rename' | null
const newName = ref('')
const newTemplate = ref('')
const renameName = ref('')
const renameTarget = ref(null)
const previewWf = ref(null)
const toast = ref('')

const filteredWorkflows = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return store.workflows
  return store.workflows.filter(w => (w.name || '').toLowerCase().includes(q) || (w.id || '').toLowerCase().includes(q))
})

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2000)
}

onMounted(async () => {
  await store.fetchWorkflows()
})

function openCreate() {
  newName.value = ''
  newTemplate.value = ''
  modal.value = 'create'
}

function renameWf(wf) {
  renameTarget.value = wf
  renameName.value = wf.name
  modal.value = 'rename'
}

function closeModal() {
  modal.value = null
}

async function confirmModal() {
  if (modal.value === 'create') {
    const id = await store.createWorkflow({ name: newName.value.trim() || undefined, template: newTemplate.value || undefined })
    showToast(`工作流已创建：${id}`)
  } else if (modal.value === 'rename') {
    await store.renameWorkflow(renameTarget.value.id, renameName.value.trim() || renameTarget.value.name)
    showToast('重命名成功')
  }
  closeModal()
}

async function toggleStatus(wf) {
  const next = wf.status === 'published' ? 'draft' : 'published'
  await store.setWorkflowStatus(wf.id, next)
  showToast(next === 'published' ? '已发布' : '已撤稿')
}

async function removeWf(wf) {
  await store.deleteWorkflow(wf.id)
  showToast('已删除')
}

function useTemplate(tplId) {
  const tpl = templates.find(t => t.id === tplId)
  openCreate()
  newTemplate.value = tplId
  newName.value = tpl ? tpl.name : ''
}

function editWf(wf) {
  store.currentWorkflow.id = wf.id
  router.push('/editor')
}
</script>
