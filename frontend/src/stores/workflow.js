import { defineStore } from 'pinia'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// ============ 节点目录（PRD §11 六大类 40 节点） ============
export const NODE_CATALOG = {
  analysis: {
    name: '测试分析与设计',
    nodes: [
      { label: '需求解析', desc: '解析需求文档，抽取可测需求点与验收条件' },
      { label: '变更影响分析', desc: '识别直接受影响模块与需回归范围' },
      { label: '代码变更驱动测试生成', desc: '基于变更生成针对性用例' },
      { label: '风险评级', desc: '输出风险等级与可解释评级依据' },
      { label: '测试策略生成', desc: '决定测试类型组合与执行深度' },
      { label: '测试用例生成', desc: '生成结构化用例集' },
      { label: '测试数据合成', desc: '生成满足约束的合成数据' },
      { label: '单元测试生成', desc: '生成可执行单元测试' },
      { label: '变异测试驱动', desc: '生成变异体评估测试套件' },
    ],
  },
  execution: {
    name: '测试执行',
    nodes: [
      { label: 'API 测试', desc: '调用接口并执行断言' },
      { label: 'UI 探索测试', desc: '自然语言驱动浏览器执行用户旅程' },
      { label: '智能浏览器自动化', desc: '浏览器智能体自主完成任务' },
      { label: '移动端图像识别', desc: '图像识别驱动 APP 自动化' },
      { label: '视觉语义回归', desc: '结构+视觉混合回归判定' },
      { label: '性能负载测试', desc: '执行负载场景采集指标' },
      { label: '安全探测', desc: '授权/注入/敏感信息探测' },
      { label: '无障碍测试', desc: '真实交互检测无障碍违规' },
      { label: '兼容性测试', desc: '跨浏览器多机型冒烟' },
      { label: '数据库一致性', desc: '校验数据状态与迁移正确性' },
      { label: '契约校验', desc: '接口规范与实现一致性' },
      { label: 'Agent 工具契约测试', desc: '枚举并校验工具清单' },
      { label: '智能体工具调用测试', desc: '测试工具调用方行为' },
      { label: '混沌工程韧性测试', desc: '注入故障验证韧性' },
      { label: '异步任务提交与轮询', desc: '提交长任务并轮询结果' },
    ],
  },
  diagnosis: {
    name: '测试诊断与修复',
    nodes: [
      { label: '失败分诊', desc: '对执行失败进行分类' },
      { label: '缺陷复现', desc: '构造最小复现路径' },
      { label: '根因定位', desc: '输出根因假设与定位' },
      { label: '自愈与修复', desc: '自动修复测试侧问题' },
      { label: '测试资产版本管理', desc: '版本变更回归检查' },
    ],
  },
  decision: {
    name: '质量评估与决策',
    nodes: [
      { label: '测试充分性评估', desc: '评估覆盖率与风险覆盖' },
      { label: '质量门禁', desc: '多维度质量信号发布裁决' },
      { label: '测试报告生成', desc: '生成差异化报告' },
      { label: '缺陷单归档', desc: '缺陷写入外部系统' },
      { label: 'AI 问答助手', desc: '知识库问答检索' },
      { label: '测试资产认证', desc: '升级认证资产' },
    ],
  },
  control: {
    name: '控制流',
    nodes: [
      { label: '条件分支', desc: '表达式或智能裁决' },
      { label: '循环迭代', desc: '遍历或重复执行' },
      { label: '并行分发', desc: '分发至多个下游并行' },
      { label: '重试兜底', desc: '失败重试与兜底分支' },
      { label: '人工审批门', desc: '挂起等待人工确认' },
      { label: '计划确认门', desc: '规划与执行间门禁' },
      { label: '汇聚等待', desc: '等待并行分支完成' },
      { label: '子工作流调用', desc: '封装子流程供调用' },
    ],
  },
  platform: {
    name: '平台基础',
    nodes: [
      { label: '开始', desc: '工作流入口' },
      { label: '结束', desc: '工作流出口' },
      { label: 'MCP 工具调用', desc: '连接外部能力' },
      { label: '脚本执行', desc: '安全沙箱内执行脚本' },
      { label: '数据工厂工具库', desc: '编码/随机/加密等工具' },
    ],
  },
}

export const ALL_NODES = Object.values(NODE_CATALOG).flatMap(c => c.nodes)

// ============ 数据契约（用于连线校验） ============
export const NODE_CONTRACTS = {
  analysis: { in: ['需求文本', '变更差异', '风险等级', '测试类型'], out: ['结构化需求点', '用例集', '风险等级', '策略'] },
  execution: { in: ['用例集', '目标地址', '负载剖面', '工具清单'], out: ['执行记录', '截图', '性能指标', '缺陷列表'] },
  diagnosis: { in: ['失败记录', '复现步骤', '执行证据'], out: ['分诊结果', '复现脚本', '根因假设', '修复补丁'] },
  decision: { in: ['覆盖率', '通过率', '安全发现', '性能达标'], out: ['门禁判定', '报告', '认证资产'] },
  control: { in: ['布尔', '数组', '变量'], out: ['分支', '迭代', '汇聚'] },
  platform: { in: ['初始参数'], out: ['输出'] },
}

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    currentWorkflow: {
      id: 'default-workflow',
      name: '我的第一个测试工作流',
      nodes: [],
      edges: [],
    },
    workflows: [],
    isLoading: false,
    isSaving: false,
  }),
  actions: {
    async fetchWorkflow(id) {
      this.isLoading = true
      try {
        const res = await api.get(`/workflows/${id}`)
        const workflow = res.data || {}
        workflow.nodes = (workflow.nodes || []).map((node) => this.normalizeNode(node))
        workflow.edges = workflow.edges || []
        this.currentWorkflow = workflow
      } catch (e) {
        console.error('加载工作流失败:', e)
      } finally {
        this.isLoading = false
      }
    },
    async fetchWorkflows() {
      try {
        const res = await api.get('/workflows')
        this.workflows = res.data || []
      } catch (e) {
        this.workflows = []
      }
    },
    async createWorkflow({ name, template }) {
      const res = await api.post('/workflows/new', { name, template })
      await this.fetchWorkflows()
      return res.data.id
    },
    async renameWorkflow(id, name) {
      await api.post(`/workflows/${id}/rename`, { name })
      await this.fetchWorkflows()
    },
    async setWorkflowStatus(id, status) {
      await api.post(`/workflows/${id}/publish`, { status })
      await this.fetchWorkflows()
    },
    async deleteWorkflow(id) {
      await api.delete(`/workflows/${id}`)
      await this.fetchWorkflows()
    },
    async saveWorkflow() {
      this.isSaving = true
      try {
        await api.post('/workflows', this.serializeWorkflow(this.currentWorkflow))
      } catch (e) {
        console.error('保存工作流失败:', e)
      } finally {
        this.isSaving = false
      }
    },
    serializeWorkflow(workflow) {
      const runtimeKeys = ['dimensions', 'computedPosition', 'handleBounds', 'selected', 'dragging', 'resizing', 'initialized', 'isParent', 'events']
      const nodes = (workflow.nodes || []).map((node) => {
        const out = { ...node }
        runtimeKeys.forEach((k) => delete out[k])
        return out
      })
      return { ...workflow, nodes }
    },
    normalizeNode(node = {}) {
      const rawCategory = node.data?.category || node.type || node.config?.type || 'platform'
      let category = rawCategory
      if (!NODE_CATALOG[category]) {
        const label0 = node.label || node.data?.label
        const found = label0 ? ALL_NODES.find((n) => n.label === label0) : null
        if (found) {
          for (const [key, c] of Object.entries(NODE_CATALOG)) {
            if (c.nodes.some((n) => n.label === found.label)) {
              category = key
              break
            }
          }
        }
        if (!NODE_CATALOG[category]) category = 'platform'
      }
      const label = node.label || node.data?.label || '未命名节点'
      return {
        ...node,
        type: 'custom',
        label,
        position: node.position || { x: 80, y: 120 },
        data: {
          ...(node.data || {}),
          category,
          label,
          desc: node.data?.desc || NODE_CATALOG[category]?.nodes.find((item) => item.label === label)?.desc || '',
          status: node.data?.status || 'pending',
        },
        config: {
          toolWhitelist: [],
          skills: [],
          rules: [],
          inputBindings: [],
          outputSchemaText: '{}',
          ...(node.config || {}),
        },
      }
    },
    addNode(category, label, desc = '') {
      const id = `n_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`
      const node = this.normalizeNode({
        id,
        type: category,
        label,
        position: { x: 120 + Math.random() * 180, y: 120 + Math.random() * 180 },
        data: { category, label, desc, status: 'pending' },
        config: {
          model: 'Agnes 3.0 Flash',
          temperature: 0.2,
          topP: 0.9,
          systemPrompt: '',
          userPrompt: '',
          inputBindings: [],
          outputSchema: {},
          toolWhitelist: [],
          skills: [],
          maxSteps: 10,
          timeoutSec: 120,
          tokenBudget: 4000,
          retry: 1,
          rules: [],
          asyncMode: false,
          resources: [],
        },
      })
      this.currentWorkflow.nodes.push(node)
      return node
    },
    addEdge(source, target, sourceHandle) {
      const id = `e_${Date.now().toString(36)}`
      this.currentWorkflow.edges.push({
        id,
        source,
        target,
        sourceHandle: sourceHandle || null,
      })
      return this.currentWorkflow.edges[this.currentWorkflow.edges.length - 1]
    },
    removeNode(id) {
      this.currentWorkflow.nodes = this.currentWorkflow.nodes.filter(n => n.id !== id)
      this.currentWorkflow.edges = this.currentWorkflow.edges.filter(
        e => e.source !== id && e.target !== id
      )
    },
    removeEdge(id) {
      this.currentWorkflow.edges = this.currentWorkflow.edges.filter(e => e.id !== id)
    },
    updateNodesPosition(nodes) {
      this.currentWorkflow.nodes = nodes
    },
    updateEdges(edges) {
      this.currentWorkflow.edges = edges
    },
  },
})

// ============ 结构校验（PRD §7.2） ============
export function validateWorkflow(workflow) {
  const issues = []
  const nodes = workflow.nodes || []
  const edges = workflow.edges || []
  const hasStart = nodes.some(n => n.data?.category === 'platform' && n.label === '开始')
  const hasEnd = nodes.some(n => n.data?.category === 'platform' && n.label === '结束')
  if (!hasStart) issues.push({ level: 'error', msg: '缺少开始节点' })
  if (!hasEnd) issues.push({ level: 'error', msg: '缺少结束节点' })
  if (nodes.length > 0 && !hasStart && !hasEnd) {
    issues.push({ level: 'error', msg: '工作流必须有且仅有一个开始节点与一个结束节点' })
  }
  // 执行类节点需有可达的下游验证节点
  const execIds = nodes.filter(n => n.data?.category === 'execution').map(n => n.id)
  const verifyIds = nodes.filter(n => ['diagnosis', 'decision'].includes(n.data?.category)).map(n => n.id)
  const downstream = (id) => {
    const out = edges.filter(e => e.source === id)
    return out.flatMap(e => [e.target, ...downstream(e.target)])
  }
  const seen = new Set()
  for (const eid of execIds) {
    if (seen.has(eid)) continue
    const reach = new Set(downstream(eid))
    seen.add(eid)
    if (![...reach].some(r => verifyIds.includes(r))) {
      issues.push({ level: 'error', msg: `执行节点「${nodes.find(n => n.id === eid)?.label}」缺少可达的下游验证节点` })
    }
  }
  // 循环节点需配置验收标准与最大迭代次数
  for (const n of nodes) {
    if (n.label === '循环迭代') {
      const cfg = n.config || {}
      if (!cfg.acceptance && !cfg.maxIterations) {
        issues.push({ level: 'error', msg: `循环节点「${n.id}」必须配置验收标准与最大迭代次数` })
      }
    }
  }
  // 异步任务需配合汇聚等待
  const asyncNode = nodes.find(n => n.label === '异步任务提交与轮询')
  const joinNode = nodes.find(n => n.label === '汇聚等待')
  if (asyncNode && !joinNode) {
    issues.push({ level: 'error', msg: '异步任务提交节点必须配合汇聚等待节点使用' })
  }
  return issues
}
