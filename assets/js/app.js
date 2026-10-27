/* ==========================================================================
   共享运行时：应用外壳 + Mock 数据仓库 + 通用交互
   ========================================================================== */

/* --------------------------------------------------------------------------
   1. 节点目录（对应 PRD §11 节点体系总览）
   -------------------------------------------------------------------------- */
const NODE_CATALOG = {
  design: {
    name: '测试分析与设计', color: 'var(--cat-design)', icon: '◈',
    nodes: [
      { id: 'req_parse', name: '需求解析', icon: '📋', desc: '解析需求文档，抽取可测需求点、验收条件与歧义标记', out: ['requirements', 'score', 'ambiguities'] },
      { id: 'impact_analysis', name: '变更影响分析', icon: '🔀', desc: '基于代码变更与依赖关系识别受影响模块与回归范围', out: ['affected_modules', 'direct_risk', 'transitive_risk', 'regression_scope'] },
      { id: 'code_change_gen', name: '代码变更驱动测试生成', icon: '🧬', desc: '基于变更影响自动生成针对性功能用例与接口用例', out: ['cases'] },
      { id: 'risk_rating', name: '风险评级', icon: '⚖️', desc: '综合变更影响、缺陷密度与业务关键性输出可解释风险等级', out: ['risk_level', 'risk_score', 'rationale'] },
      { id: 'strategy_gen', name: '测试策略生成', icon: '🗺️', desc: '决定测试类型组合、执行深度、跳过决策与资源分配', out: ['test_types', 'depth', 'skip_decisions', 'estimate'] },
      { id: 'case_gen', name: '测试用例生成', icon: '📝', desc: '生成覆盖正常/边界/异常/状态迁移的结构化测试用例', out: ['cases', 'coverage_note'] },
      { id: 'data_synth', name: '测试数据合成', icon: '🎲', desc: '生成合法值、边界值与异常值合成数据，支持固定种子复现', out: ['datasets', 'compliance_note'] },
      { id: 'unit_test_gen', name: '单元测试生成', icon: '🔬', desc: '生成可执行单元测试，以变异分数与覆盖率作为质量信号', out: ['unit_tests', 'quality_signal', 'gaps'] },
      { id: 'mutation_test', name: '变异测试驱动', icon: '🧟', desc: '生成变异体评估测试套件缺陷检测能力，驱动断言强化', out: ['mutants', 'survivors', 'suggestions'] },
    ]
  },
  execute: {
    name: '测试执行', color: 'var(--cat-execute)', icon: '▶',
    nodes: [
      { id: 'api_test', name: 'API / 接口测试执行', icon: '🔌', desc: '调用接口、记录请求响应、执行断言与判定', out: ['records', 'summary'] },
      { id: 'ui_explore', name: 'UI 探索测试', icon: '🖱️', desc: '自然语言意图驱动浏览器执行用户旅程', out: ['steps', 'screenshots', 'issues', 'a11y'] },
      { id: 'browser_use', name: 'Browser-use 智能浏览器自动化', icon: '🌐', desc: '浏览器智能体自主理解页面并完成非脚本化探索任务', out: ['steps', 'verdict', 'evidence'] },
      { id: 'airtest', name: 'Airtest 移动端图像识别自动化', icon: '📱', desc: '图像识别驱动移动应用执行测试与控件操作', out: ['steps', 'recordings', 'issues'] },
      { id: 'visual_regression', name: '视觉 / 语义回归', icon: '👁️', desc: '结合无障碍树与多模态视觉做混合像素与语义断言', out: ['diffs', 'diff_types', 'evidence'] },
      { id: 'perf_test', name: '性能负载测试', icon: '🚀', desc: '执行负载场景，采集延迟、吞吐、错误率与资源饱和度', out: ['profile', 'metrics', 'violations', 'bottleneck'] },
      { id: 'security_scan', name: '安全探测', icon: '🛡️', desc: '授权绕过、注入、敏感信息泄露等探测，内置破坏性熔断', out: ['findings', 'confidence', 'scope_note'] },
      { id: 'a11y_test', name: '无障碍测试', icon: '♿', desc: '真实浏览器交互中检测无障碍规范违规', out: ['violations', 'severity', 'fixes'] },
      { id: 'compat_test', name: '兼容性测试', icon: '🧩', desc: '跨浏览器、多机型、多环境冒烟遍历与差异发现', out: ['results', 'diffs', 'risk'] },
      { id: 'db_consistency', name: '数据库 / 数据一致性', icon: '🗄️', desc: '校验测试前后数据状态、事务完整性与迁移正确性', out: ['results', 'verdict', 'diffs'] },
      { id: 'contract_check', name: '契约校验', icon: '📄', desc: '校验接口规范与实现的一致性', out: ['deviations', 'compatibility', 'impact'] },
      { id: 'agent_tool_contract', name: 'Agent 工具契约测试', icon: '🔌', desc: '枚举注册工具清单，校验完整性与参数结构兼容性', out: ['manifest_diff', 'schema_verdict', 'evidence'] },
      { id: 'agent_tool_call', name: '智能体工具调用测试', icon: '🕹️', desc: '测试被测应用作为工具调用方时的行为正确性', out: ['call_seq', 'structure_verdict', 'error_handling'] },
      { id: 'chaos_test', name: '混沌工程 / 韧性测试', icon: '🌊', desc: '注入延迟、熔断、依赖不可用验证系统韧性', out: ['injections', 'response', 'recovery_time', 'verdict'] },
      { id: 'async_task', name: '异步任务提交与轮询', icon: '⏳', desc: '提交长时任务立即返回标识，通过轮询或回调获取结果', out: ['task_id', 'submit_status', 'result_ref'] },
    ]
  },
  diagnose: {
    name: '测试诊断与修复', color: 'var(--cat-diagnose)', icon: '✚',
    nodes: [
      { id: 'triage', name: '失败分诊', icon: '🩺', desc: '将失败分类为产品缺陷/测试缺陷/环境/不稳定/数据问题', out: ['classification', 'confidence', 'routing'] },
      { id: 'reproduce', name: '缺陷复现', icon: '♻️', desc: '构造最小复现路径并生成可执行复现脚本与证据包', out: ['min_steps', 'script', 'evidence', 'score'] },
      { id: 'root_cause', name: '根因定位', icon: '🔎', desc: '结合失败证据与运行时信号输出根因假设与定位组件', out: ['hypothesis', 'confidence', 'component', 'contributing'] },
      { id: 'self_heal', name: '自愈与修复', icon: '🩹', desc: '自动修复测试侧问题或生成产品修复建议补丁', out: ['fix_type', 'changes', 'risk', 'verify_plan'] },
      { id: 'asset_version', name: '测试资产版本管理与副作用回归', icon: '📦', desc: '对能力包版本变更做回归检查，判定是否允许升级', out: ['impact', 'regression', 'verdict'] },
    ]
  },
  quality: {
    name: '质量评估与决策', color: 'var(--cat-quality)', icon: '★',
    nodes: [
      { id: 'sufficiency', name: '测试充分性评估', icon: '🧮', desc: '评估需求/代码/风险覆盖率并识别未覆盖盲区', out: ['coverage', 'blind_spots', 'verdict'] },
      { id: 'quality_gate', name: '质量门禁', icon: '🚦', desc: '规则引擎确定性裁决 + 模型归因叙述，双阶段判定', out: ['verdict', 'basis', 'narrative', 'blockers'] },
      { id: 'report_gen', name: '测试报告生成', icon: '📑', desc: '汇总结构化输出，生成工程/管理/合规三类受众视图', out: ['report', 'charts', 'refs'] },
      { id: 'defect_archive', name: '缺陷单归档', icon: '📮', desc: '将确认缺陷结构化写入外部缺陷追踪系统', out: ['defect_id', 'archive_status', 'evidence'] },
      { id: 'qa_assistant', name: 'AI 问答助手', icon: '💬', desc: '基于知识库检索问答，为下游节点注入测试规范与历史缺陷', out: ['answer', 'sources'] },
      { id: 'asset_certify', name: '测试资产认证', icon: '🏅', desc: '规则引擎结合质量门槛判定资产认证或阻断', out: ['asset_id', 'cert_status', 'evidence', 'scope', 'version'] },
    ]
  },
  control: {
    name: '控制流', color: 'var(--cat-control)', icon: '⑂',
    nodes: [
      { id: 'condition', name: '条件分支', icon: '🔀', desc: '表达式或智能裁决模式路由，裁决依据可追溯', out: ['branch'] },
      { id: 'loop', name: '循环 / 迭代', icon: '🔁', desc: '数组遍历或条件重复执行，强制配置验收标准与最大迭代', out: ['iterations'] },
      { id: 'parallel', name: '并行分发', icon: '⤴️', desc: '将同一输入分发至多个下游节点并行执行', out: ['branches'] },
      {invoke: true, id: 'retry', name: '重试 / 兜底', icon: '♻️', desc: '定义重试次数、退避策略与失败兜底分支', out: ['result'] },
      { id: 'approval', name: '人工审批门', icon: '✋', desc: '挂起工作流等待人工确认，审批记录不可篡改', out: ['approved'] },
      { id: 'plan_gate', name: '计划确认门', icon: '🚦', desc: '规划与执行间的串行门禁，对规划输出执行契约校验', out: ['passed', 'violations'] },
      { id: 'join', name: '汇聚等待', icon: '🔗', desc: '等待所有并行分支（含异步任务）完成后继续', out: ['merged'] },
      { id: 'subflow', name: '子工作流调用', icon: '📦', desc: '将可复用节点序列封装为子流程供其他工作流调用', out: ['sub_result'] },
    ]
  },
  base: {
    name: '平台基础', color: 'var(--cat-base)', icon: '◻',
    nodes: [
      { id: 'start', name: '开始', icon: '▶', desc: '工作流入口，定义触发所需的初始参数', out: ['params'] },
      { id: 'end', name: '结束', icon: '■', desc: '工作流出口，汇总指定节点输出作为最终结果', out: ['result'] },
      { id: 'mcp_call', name: 'MCP / WebMCP 工具调用', icon: '🔌', desc: '连接外部能力的标准化通道，接入外部服务与数据源', out: ['response'] },
      { id: 'script', name: '脚本执行', icon: '📜', desc: '在安全沙箱中执行注入的自定义脚本代码', out: ['result'] },
      { id: 'data_factory', name: '数据工厂工具库', icon: '🏭', desc: '提供编码、随机生成、加密解密、格式转换等实用工具', out: ['value'] },
    ]
  }
};

const ALL_NODES = {};
Object.entries(NODE_CATALOG).forEach(([cat, g]) => {
  g.nodes.forEach(n => { ALL_NODES[n.id] = Object.assign({ cat }, n); });
});
/* 修正个别笔误 */
if (ALL_NODES.retry) delete ALL_NODES.retry.invoke;

const CAT_META = {
  design:   { name: '测试分析与设计', color: 'var(--cat-design)', hex: '#6366f1' },
  execute:  { name: '测试执行',       color: 'var(--cat-execute)', hex: '#06b6d4' },
  diagnose: { name: '测试诊断与修复', color: 'var(--cat-diagnose)', hex: '#f59e0b' },
  quality:  { name: '质量评估与决策', color: 'var(--cat-quality)', hex: '#a855f7' },
  control:  { name: '控制流',         color: 'var(--cat-control)', hex: '#ec4899' },
  base:     { name: '平台基础',       color: 'var(--cat-base)', hex: '#64748b' },
};

/* --------------------------------------------------------------------------
   2. 工作流数据
   -------------------------------------------------------------------------- */
const WORKFLOWS = [
  { id: 'wf_cicd', name: '代码变更驱动的 CI/CD 质量门禁', status: 'published', updated: '2026-10-20 16:42', owner: '雪 樱', nodes: 16, edges: 17, runs: 128, pass: 0.86, tags: ['CI/CD', '质量门禁'], desc: '变更分析 → 风险评级 → 用例生成 → 多类型并行执行 → 门禁裁决' },
  { id: 'wf_explore', name: '智能探索与大规模异步回归', status: 'published', updated: '2026-10-19 10:08', owner: '李 明', nodes: 12, edges: 11, runs: 64, pass: 0.78, tags: ['探索测试', '异步'], desc: '策略生成 → 浏览器智能体探索 + 异步大规模回归并行' },
  { id: 'wf_mobile', name: '移动端多端回归', status: 'published', updated: '2026-10-18 21:33', owner: '王 强', nodes: 11, edges: 10, runs: 47, pass: 0.91, tags: ['移动端', '兼容性'], desc: '设备 A/B/Web 并行执行，资源锁保证设备独占' },
  { id: 'wf_design', name: '需求到用例的测试设计流水线', status: 'draft', updated: '2026-10-20 09:15', owner: '雪 樱', nodes: 9, edges: 8, runs: 12, pass: 0.92, tags: ['测试设计'], desc: '需求解析 → 用例生成 → 数据合成 → 充分性评估 → 资产认证' },
  { id: 'wf_api', name: '核心接口每日巡检', status: 'published', updated: '2026-10-17 08:50', owner: '陈 晨', nodes: 8, edges: 7, runs: 212, pass: 0.97, tags: ['接口测试', '定时'], desc: '接口用例集每日定时执行，异常自动分诊' },
  { id: 'wf_sec', name: '安全基线扫描流水线', status: 'draft', updated: '2026-10-15 14:20', owner: '李 明', nodes: 10, edges: 9, runs: 5, pass: 0.8, tags: ['安全'], desc: '授权范围内的安全探测与红线下规则校验' },
  { id: 'wf_perf', name: '大促前性能压测基线', status: 'draft', updated: '2026-10-14 11:02', owner: '王 强', nodes: 9, edges: 8, runs: 3, pass: 1, tags: ['性能'], desc: '负载剖面生成与动态调载，压测结果回写' },
  { id: 'wf_a11y', name: '无障碍合规巡检', status: 'published', updated: '2026-10-11 17:40', owner: '陈 晨', nodes: 7, edges: 6, runs: 36, pass: 0.94, tags: ['无障碍', '合规'], desc: '真实浏览器交互检测 + 违规修复建议' },
];

const RUNS = [
  { id: 'run_20261020_1642', wf: 'wf_cicd', wfName: '代码变更驱动的 CI/CD 质量门禁', ver: 'v12', status: 'success', trigger: 'Git Push', triggerIcon: '⎇', started: '2026-10-20 16:42:11', dur: '6m 18s', cost: 4.82, tokens: 618204, gate: '有条件通过', by: '雪 樱', branch: 'feature/order-refactor' },
  { id: 'run_20261020_1601', wf: 'wf_cicd', wfName: '代码变更驱动的 CI/CD 质量门禁', ver: 'v12', status: 'success', trigger: 'Git Push', triggerIcon: '⎇', started: '2026-10-20 16:01:03', dur: '5m 52s', cost: 4.51, tokens: 584102, gate: '通过', by: '雪 樱', branch: 'feature/order-refactor' },
  { id: 'run_20261020_1433', wf: 'wf_explore', wfName: '智能探索与大规模异步回归', ver: 'v8', status: 'failed', trigger: '定时调度', triggerIcon: '⏱', started: '2026-10-20 14:33:00', dur: '18m 04s', cost: 12.37, tokens: 1930488, gate: '阻断', by: '李 明', branch: 'main' },
  { id: 'run_20261020_1120', wf: 'wf_cicd', wfName: '代码变更驱动的 CI/CD 质量门禁', ver: 'v11', status: 'success', trigger: '外部 Agent 调用', triggerIcon: '⇄', started: '2026-10-20 11:20:45', dur: '6m 41s', cost: 5.12, tokens: 671903, gate: '通过', by: '外部系统', branch: 'release/2.4' },
  { id: 'run_20261019_2210', wf: 'wf_mobile', wfName: '移动端多端回归', ver: 'v5', status: 'success', trigger: '手动执行', triggerIcon: '▶', started: '2026-10-19 22:10:22', dur: '22m 37s', cost: 9.63, tokens: 1244119, gate: '通过', by: '王 强', branch: 'main' },
  { id: 'run_20261019_1930', wf: 'wf_cicd', wfName: '代码变更驱动的 CI/CD 质量门禁', ver: 'v11', status: 'failed', trigger: 'Git Push', triggerIcon: '⎇', started: '2026-10-19 19:30:07', dur: '4m 58s', cost: 4.06, tokens: 529884, gate: '阻断', by: '雪 樱', branch: 'feature/checkout-v2' },
  { id: 'run_20261019_0900', wf: 'wf_api', wfName: '核心接口每日巡检', ver: 'v3', status: 'success', trigger: '定时调度', triggerIcon: '⏱', started: '2026-10-19 09:00:00', dur: '2m 11s', cost: 0.42, tokens: 52311, gate: '通过', by: '系统', branch: 'main' },
  { id: 'run_20261018_1500', wf: 'wf_a11y', wfName: '无障碍合规巡检', ver: 'v2', status: 'running', trigger: '定时调度', triggerIcon: '⏱', started: '2026-10-18 15:00:00', dur: '运行中', cost: 1.20, tokens: 154773, gate: '—', by: '系统', branch: 'main' },
];

/* --------------------------------------------------------------------------
   3. 认证资产库
   -------------------------------------------------------------------------- */
const ASSETS = [
  { id: 'AST-1042', name: '订单创建主流程回归用例集', type: '认证用例', ver: 'v3.2', scope: ['订单中心', '电商'], status: 'certified', quality: 98, mutation: 0.92, stability: 0.99, owner: '雪 樱', updated: '2026-10-18', use: 142, suites: 4 },
  { id: 'AST-1038', name: '用户中心接口自动化脚本', type: '认证自动化脚本', ver: 'v2.1', scope: ['用户中心'], status: 'certified', quality: 95, mutation: 0.88, stability: 0.97, owner: '李 明', updated: '2026-10-16', use: 89, suites: 2 },
  { id: 'AST-1035', name: '支付异常场景数据模板', type: '认证测试数据模板', ver: 'v1.4', scope: ['支付'], status: 'certified', quality: 91, mutation: 0.76, stability: 0.96, owner: '陈 晨', updated: '2026-10-14', use: 57, suites: 3 },
  { id: 'AST-1030', name: '通用鉴权与权限校验能力包', type: '认证能力包', ver: 'v4.0', scope: ['全平台'], status: 'certified', quality: 99, mutation: 0.95, stability: 0.99, owner: '王 强', updated: '2026-10-12', use: 213, suites: 9 },
  { id: 'AST-1027', name: '登录与验证码风控能力包', type: '认证能力包', ver: 'v1.9', scope: ['账号'], status: 'stale', quality: 64, mutation: 0.51, stability: 0.72, owner: '李 明', updated: '2026-08-30', use: 31, suites: 2 },
  { id: 'AST-1024', name: '商品列表分页接口用例', type: '代码变更驱动的生成用例', ver: 'v1.0', scope: ['商品'], status: 'pending', quality: 72, mutation: 0.44, stability: 0.81, owner: '雪 樱', updated: '2026-10-19', use: 0, suites: 0 },
  { id: 'AST-1019', name: '移动端兼容矩阵遍历脚本', type: '认证自动化脚本', ver: 'v2.6', scope: ['移动端'], status: 'certified', quality: 93, mutation: 0.83, stability: 0.94, owner: '王 强', updated: '2026-10-09', use: 76, suites: 5 },
  { id: 'AST-1015', name: '购物车金额一致性断言集', type: '认证用例', ver: 'v1.7', scope: ['购物车'], status: 'certified', quality: 96, mutation: 0.89, stability: 0.98, owner: '陈 晨', updated: '2026-10-05', use: 64, suites: 3 },
];

/* --------------------------------------------------------------------------
   4. 异步任务
   -------------------------------------------------------------------------- */
const TASKS = [
  { id: 'TSK-9F2A', name: '全量回归 — 订单中心 v2.4', type: '大规模回归', status: 'running', wf: '智能探索与大规模异步回归', node: '异步任务提交与轮询', progress: 0.68, started: '2026-10-20 14:33:12', eta: '约 8 分钟', owner: '李 明', resource: '资源池 mobile-01' },
  { id: 'TSK-9F29', name: '安全基线全量扫描', type: '安全扫描', status: 'running', wf: '安全基线扫描流水线', node: '异步任务提交与轮询', progress: 0.34, started: '2026-10-20 15:52:40', eta: '约 21 分钟', owner: '李 明', resource: '扫描集群 sec-02' },
  { id: 'TSK-9F26', name: '大促压测 — 峰值 8k QPS', type: '多机压测', status: 'success', wf: '大促前性能压测基线', node: '异步任务提交与轮询', progress: 1, started: '2026-10-20 13:10:00', eta: '已完成', owner: '王 强', resource: '压测集群 perf-01' },
  { id: 'TSK-9F21', name: '多机型兼容遍历（8 设备）', type: '兼容性回归', status: 'success', wf: '移动端多端回归', node: '异步任务提交与轮询', progress: 1, started: '2026-10-19 22:10:00', eta: '已完成', owner: '王 强', resource: '设备池 8 台' },
  { id: 'TSK-9F18', name: '全量 UI 回归 — 商家后台', type: '大规模回归', status: 'failed', wf: '智能探索与大规模异步回归', node: '异步任务提交与轮询', progress: 0.46, started: '2026-10-19 14:02:00', eta: '已失败', owner: '李 明', resource: '资源池 web-03' },
  { id: 'TSK-9F11', name: '压测基线采集 — 常态流量', type: '压测', status: 'timeout', wf: '大促前性能压测基线', node: '异步任务提交与轮询', progress: 0.81, started: '2026-10-19 09:00:00', eta: '已超时', owner: '王 强', resource: '压测集群 perf-02' },
  { id: 'TSK-9F05', name: '认证资产副作用回归检查', type: '副作用回归', status: 'success', wf: '测试资产版本管理与副作用回归', node: '异步任务提交与轮询', progress: 1, started: '2026-10-18 16:20:00', eta: '已完成', owner: '雪 樱', resource: '—' },
];

/* --------------------------------------------------------------------------
   5. 模型配置与额度
   -------------------------------------------------------------------------- */
const MODELS = [
  { id: 'mdl_1', name: 'GPT-4o', provider: 'OpenAI', scope: '全站默认', text: true, vision: true, status: 'active', used: 62, cost: 41.2, temp: 0.3, topP: 0.9 },
  { id: 'mdl_2', name: 'Claude Sonnet 4', provider: 'Anthropic', scope: '全站默认', text: true, vision: true, status: 'active', used: 24, cost: 33.8, temp: 0.3, topP: 0.9 },
  { id: 'mdl_3', name: 'Qwen-Max', provider: '阿里云', scope: '个人配置', text: true, vision: true, status: 'active', used: 8, cost: 14.2, temp: 0.4, topP: 0.9 },
  { id: 'mdl_4', name: 'DeepSeek-V3', provider: 'DeepSeek', scope: '个人配置', text: true, vision: false, status: 'active', used: 5, cost: 2.1, temp: 0.5, topP: 0.95 },
  { id: 'mdl_5', name: 'Qwen2.5-VL-72B', provider: '阿里云', scope: '按角色配置', text: true, vision: true, status: 'active', used: 0, cost: 0, temp: 0.2, topP: 0.9, role: '视觉回归节点' },
  { id: 'mdl_6', name: 'GLM-4-Plus', provider: '智谱', scope: '个人配置', text: true, vision: false, status: 'error', used: 2, cost: 0.6, temp: 0.3, topP: 0.9 },
];

const QUOTAS = [
  { id: 'q1', account: '雪 樱', avatar: '雪', type: '自然日叠加', amount: 50, used: 12, granted: '2026-10-20 08:00', by: '管理员 · 张总', state: 'active', note: '大促期间临时扩容' },
  { id: 'q2', account: '李 明', avatar: '李', type: '自然日叠加', amount: 30, used: 30, granted: '2026-10-20 08:00', by: '管理员 · 张总', state: 'exhausted', note: '安全扫描任务额度' },
  { id: 'q3', account: '王 强', avatar: '王', type: '自然日叠加', amount: 30, used: 8, granted: '2026-10-19 08:00', by: '管理员 · 张总', state: 'active', note: '' },
  { id: 'q4', account: '陈 晨', avatar: '陈', type: '自然日叠加', amount: 20, used: 0, granted: '2026-10-18 08:00', by: '雪 樱', state: 'revoked', note: '已撤销' },
];

/* --------------------------------------------------------------------------
   6. 审计 / 证据账本
   -------------------------------------------------------------------------- */
const AUDIT = [
  { id: 'EVT-88213', ts: '2026-10-20 16:42:11', type: '工作流运行', actor: '雪 樱', target: '代码变更驱动的 CI/CD 质量门禁 #v12', result: 'success', hash: '0x7f3a…c918', detail: '触发 16 个节点，1 次人工审批门通过' },
  { id: 'EVT-88212', ts: '2026-10-20 16:41:52', type: '工具调用', actor: '质量门禁节点', target: 'rule-engine.gate.evaluate', result: 'success', hash: '0x91b2…4e07', detail: '判定依据：API 通过率 98.2%，安全发现 1 项低危' },
  { id: 'EVT-88211', ts: '2026-10-20 16:40:08', type: '白名单拒绝', actor: 'UI 探索测试节点', target: 'shell.exec', result: 'denied', hash: '0x2fd0…a912', detail: '工具不在白名单内，已拦截并记录' },
  { id: 'EVT-88210', ts: '2026-10-20 16:39:44', type: '人工审批', actor: '李 明', target: '计划确认门 · 订单支付链路', result: 'approved', hash: '0x5c11…8b34', detail: '审批意见：同意进入执行阶段' },
  { id: 'EVT-88209', ts: '2026-10-20 16:38:02', type: '外部调用', actor: '外部 Agent · dev-bot', target: 'POST /api/v1/workflows/wf_cicd/run', result: 'success', hash: '0xd9e0…3f77', detail: '鉴权通过，角色 scope:workflow:run' },
  { id: 'EVT-88208', ts: '2026-10-20 16:22:15', type: '缺陷归档', actor: '缺陷单归档节点', target: 'JIRA-4471', result: 'success', hash: '0x33aa…90c1', detail: '关联证据 7 条（分诊/复现/根因）' },
  { id: 'EVT-88207', ts: '2026-10-20 16:18:33', type: '裁决升级', actor: '风险评级节点', target: '风险等级 P0 → 人工复核', result: 'escalated', hash: '0xa17b…5d2e', detail: '风险分 87，超过自动处置阈值 80' },
  { id: 'EVT-88206', ts: '2026-10-20 15:52:40', type: '任务提交', actor: '异步任务提交与轮询节点', target: 'TSK-9F29 安全基线全量扫描', result: 'success', hash: '0xbe40…9a25', detail: '持有资源锁 scan-cluster/sec-02' },
  { id: 'EVT-88205', ts: '2026-10-20 14:33:12', type: '资源锁', actor: '调度器', target: '资源池 mobile-01', result: 'acquired', hash: '0x6c8d…1f04', detail: '独占锁，TTL 3600s' },
  { id: 'EVT-88204', ts: '2026-10-20 14:30:05', type: '资产认证', actor: '测试资产认证节点', target: 'AST-1024 商品列表分页接口用例', result: 'blocked', hash: '0x47f2…bb68', detail: '变异分数 0.44 低于门槛 0.70' },
];

const CAPABILITIES = [
  { id: 'cap_1', name: 'CI/CD 质量门禁（只读）', desc: '触发质量门禁工作流并返回裁决结果，不写入缺陷', type: '工作流', vis: 'public', auth: 'Bearer Key', calls: 284, last: '2026-10-20 16:38', status: 'active', scope: 'workflow:run, result:read' },
  { id: 'cap_2', name: '智能浏览器探索执行', desc: '以自然语言任务驱动浏览器智能体完成探索测试', type: '节点', vis: 'private', auth: 'Bearer Key', calls: 96, last: '2026-10-20 11:12', status: 'active', scope: 'node:execute' },
  { id: 'cap_3', name: '缺陷单写入', desc: '将确认缺陷写入外部缺陷追踪系统（默认进入审批队列）', type: '节点', vis: 'private', auth: 'Bearer Key', calls: 31, last: '2026-10-20 16:22', status: 'active', scope: 'defect:write' },
  { id: 'cap_4', name: '认证资产检索', desc: '按关键字与适用范围检索认证资产，供外部 Agent 复用', type: '平台能力', vis: 'public', auth: 'OAuth2', calls: 512, last: '2026-10-20 15:44', status: 'active', scope: 'asset:read' },
  { id: 'cap_5', name: '压测任务提交', desc: '提交性能压测异步任务，返回任务标识', type: '节点', vis: 'private', auth: 'Bearer Key', calls: 17, last: '2026-10-19 22:40', status: 'paused', scope: 'node:execute' },
];

const RESOURCES = [
  { id: 'res_1', name: 'mobile-01', type: '设备', mode: '独占锁', holder: 'TSK-9F2A', holderType: '异步任务', acquired: '2026-10-20 14:33', ttl: '58 分钟', state: 'busy' },
  { id: 'res_2', name: 'mobile-02', type: '设备', mode: '独占锁', holder: '—', holderType: '', acquired: '—', ttl: '—', state: 'idle' },
  { id: 'res_3', name: 'web-03', type: '浏览器容器', mode: '共享锁 (3/5)', holder: 'run_20261020_1642', holderType: '工作流运行', acquired: '2026-10-20 16:42', ttl: '11 分钟', state: 'busy' },
  { id: 'res_4', name: 'sec-02', type: '扫描集群', mode: '独占锁', holder: 'TSK-9F29', holderType: '异步任务', acquired: '2026-10-20 15:52', ttl: '1 小时 52 分', state: 'busy' },
  { id: 'res_5', name: 'perf-01', type: '压测集群', mode: '独占锁', holder: '—', holderType: '', acquired: '—', ttl: '—', state: 'idle' },
  { id: 'res_6', name: 'staging-env', type: '测试环境', mode: '共享锁 (8/20)', holder: '多个工作流', holderType: '', acquired: '2026-10-20 08:00', ttl: '不限', state: 'busy' },
  { id: 'res_7', name: 'cred-pay-prod', type: '凭据', mode: '独占锁', holder: '—', holderType: '', acquired: '—', ttl: '—', state: 'idle' },
];

/* --------------------------------------------------------------------------
   7. 导航结构
   -------------------------------------------------------------------------- */
const NAV = [
  { group: '工作台', items: [
    { id: 'dashboard', label: '总览', icon: '◱', href: 'dashboard.html' },
    { id: 'workflows', label: '工作流', icon: '⑆', href: 'workflows.html', badge: '8' },
  ]},
  { group: '编排', items: [
    { id: 'editor', label: '编排画布', icon: '◈', href: 'editor.html' },
    { id: 'assets', label: '认证资产库', icon: '🏅', href: 'assets.html', badge: '8' },
  ]},
  { group: '运行', items: [
    { id: 'runs', label: '执行追踪', icon: '⏱', href: 'runs.html', badge: '8' },
    { id: 'tasks', label: '异步任务', icon: '⏳', href: 'tasks.html', badge: '3' },
  ]},
  { group: '治理', items: [
    { id: 'models', label: '模型与额度', icon: '◑', href: 'models.html' },
    { id: 'audit', label: '审计账本', icon: '🛡', href: 'audit.html' },
    { id: 'capabilities', label: '开放能力', icon: '⇄', href: 'capabilities.html' },
  ]},
  { group: '系统', items: [
    { id: 'resources', label: '资源与锁', icon: '🔒', href: 'resources.html' },
    { id: 'settings', label: '配置中心', icon: '⚙', href: 'settings.html' },
  ]},
];

/* --------------------------------------------------------------------------
   8. 通用工具
   -------------------------------------------------------------------------- */
const $  = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function money(n) { return '$' + Number(n || 0).toFixed(2); }
function num(n) { return Number(n || 0).toLocaleString('en-US'); }
function pct(n) { return (Number(n || 0) * 100).toFixed(1) + '%'; }

function statusTag(s) {
  const map = {
    success: ['ok', '成功'], ok: ['ok', '成功'], active: ['ok', '运行中'], certified: ['ok', '已认证'],
    published: ['ok', '已发布'], running: ['info', '运行中'], pending: ['warn', '待处理'], draft: ['', '草稿'],
    failed: ['err', '失败'], error: ['err', '异常'], timeout: ['err', '超时'], denied: ['err', '已拒绝'],
    stale: ['warn', '可能失效'], blocked: ['err', '阻断'], escalated: ['warn', '已升级'],
    exhausted: ['err', '已用尽'], revoked: ['', '已撤销'], paused: ['', '已暂停'], idle: ['', '空闲'], busy: ['info', '占用中'],
    approved: ['ok', '已通过'], acquired: ['info', '已获取'],
  };
  const m = map[s] || ['', s];
  return `<span class="tag ${m[0]} dot">${esc(m[1])}</span>`;
}

/* Toast */
function toast(msg, type) {
  let w = $('.toast-wrap');
  if (!w) { w = document.createElement('div'); w.className = 'toast-wrap'; document.body.appendChild(w); }
  const icons = { ok: '✓', err: '✕', warn: '!', info: 'i' };
  const t = document.createElement('div');
  t.className = 'toast ' + (type || 'ok');
  t.innerHTML = `<span class="ico">${icons[type] || '✓'}</span><span>${esc(msg)}</span>`;
  w.appendChild(t);
  setTimeout(() => { t.style.transition = 'opacity .25s, transform .25s'; t.style.opacity = '0'; t.style.transform = 'translateY(-8px)'; setTimeout(() => t.remove(), 260); }, 2400);
}

/* Modal */
function openModal(html, opts) {
  opts = opts || {};
  const mask = document.createElement('div');
  mask.className = 'modal-mask show';
  mask.innerHTML = `<div class="modal ${opts.size || ''}">${html}</div>`;
  document.body.appendChild(mask);
  const close = () => { mask.remove(); opts.onClose && opts.onClose(); };
  mask.addEventListener('click', e => { if (e.target === mask && opts.dismissible !== false) close(); });
  $$('.x, [data-close]', mask).forEach(b => b.addEventListener('click', close));
  return { el: mask, close };
}

/* Drawer */
function openDrawer(html, opts) {
  opts = opts || {};
  const mask = document.createElement('div');
  mask.className = 'drawer-mask';
  const d = document.createElement('div');
  d.className = 'drawer' + (opts.wide ? ' wide' : '');
  d.innerHTML = html;
  document.body.appendChild(mask);
  document.body.appendChild(d);
  requestAnimationFrame(() => { mask.classList.add('show'); d.classList.add('show'); });
  const close = () => {
    mask.classList.remove('show'); d.classList.remove('show');
    setTimeout(() => { mask.remove(); d.remove(); }, 280);
    opts.onClose && opts.onClose();
  };
  mask.addEventListener('click', close);
  return { el: d, mask, close };
}

/* Tabs */
function initTabs(root) {
  const scope = root || document;
  $$('.tab', scope).forEach(tab => {
    tab.addEventListener('click', () => {
      const group = tab.closest('.tabs');
      $$('.tab', group).forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const panelGroup = group.parentElement;
      const target = tab.dataset.tab;
      $$('.tab-panel', panelGroup).forEach(p => {
        p.classList.toggle('active', p.dataset.panel === target);
      });
    });
  });
}

/* 下拉菜单 */
function initMenus() {
  document.addEventListener('click', e => {
    const trigger = e.target.closest('[data-menu]');
    $$('.menu.show').forEach(m => { if (!trigger || m.dataset.for !== trigger.dataset.menu) m.classList.remove('show'); });
    if (trigger) {
      e.preventDefault(); e.stopPropagation();
      const menu = $(`#menu-${trigger.dataset.menu}`);
      if (!menu) return;
      const r = trigger.getBoundingClientRect();
      menu.style.top = (r.bottom + 5) + 'px';
      menu.style.left = Math.min(r.left, window.innerWidth - menu.offsetWidth - 12) + 'px';
      menu.classList.toggle('show');
    }
  });
  document.addEventListener('click', e => {
    const item = e.target.closest('.menu-item');
    if (item && item.dataset.action) {
      item.closest('.menu').classList.remove('show');
      item.dataset.action === 'noop' ? null : null;
    }
  });
}

/* 搜索过滤 */
function initFilter(inputSel, targetSel, key) {
  const inp = $(inputSel);
  if (!inp) return;
  inp.addEventListener('input', () => {
    const q = inp.value.trim().toLowerCase();
    $$(targetSel).forEach(el => {
      const hay = key ? (el.dataset[key] || '') : el.textContent;
      el.style.display = !q || hay.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}

/* 外壳渲染 */
function renderShell(active, opts) {
  opts = opts || {};
  const side = document.querySelector('.side');
  if (side) {
    side.innerHTML = NAV.map(g => `
      <div class="side-section">
        <div class="side-heading">${esc(g.group)}</div>
        ${g.items.map(i => `<a class="side-link ${i.id === active ? 'active' : ''}" href="${i.href}" data-nav="${i.id}">
          <span class="ico">${i.icon}</span><span>${esc(i.label)}</span>
          ${i.badge ? `<span class="badge">${i.badge}</span>` : ''}
        </a>`).join('')}
      </div>`).join('') + `<div class="side-sep"></div>
      <div class="side-section">
        <div class="side-heading">当前账号</div>
        <div class="side-link" style="cursor:default">
          <span class="ico" style="background:var(--brand-500);color:#fff;border-radius:5px;width:15px;height:15px;display:grid;place-items:center;font-size:9px;font-weight:700">雪</span>
          <span>雪 樱 · 测试架构师</span>
        </div>
      </div>`;
  }
  const tb = document.querySelector('.topbar');
  if (tb && opts.title) {
    tb.innerHTML = `
      <div class="topbar-title">
        <h1>${esc(opts.title)}</h1>
        ${opts.sub ? `<span class="tag">${esc(opts.sub)}</span>` : ''}
      </div>
      <div class="topbar-spacer"></div>
      ${opts.actions || ''}`;
  }
  initMenus();
}

/* 表格排序/筛选辅助 */
function makeSortable(table) {
  if (!table) return;
  $$('th[data-sort]', table).forEach(th => {
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const idx = th.cellIndex;
      const asc = th.dataset.dir !== 'asc';
      $$('th', table).forEach(t => t.removeAttribute('data-dir'));
      th.dataset.dir = asc ? 'asc' : 'desc';
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.rows);
      rows.sort((a, b) => {
        const av = a.cells[idx].dataset.val ?? a.cells[idx].textContent.trim();
        const bv = b.cells[idx].dataset.val ?? b.cells[idx].textContent.trim();
        const an = parseFloat(av), bn = parseFloat(bv);
        if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
        return asc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
      });
      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

/* 数字滚动 */
function animateNumber(el, to, dur, fmt) {
  const from = parseFloat(el.textContent) || 0;
  const t0 = performance.now();
  fmt = fmt || (v => Math.round(v).toLocaleString('en-US'));
  function step(t) {
    const k = Math.min(1, (t - t0) / (dur || 700));
    const e = 1 - Math.pow(1 - k, 3);
    el.textContent = fmt(from + (to - from) * e);
    if (k < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* 全局文档初始化 */
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initMenus();
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      const d = $('.drawer.show');
      if (d) { const m = $('.drawer-mask.show'); m && m.click(); return; }
      const m = $('.modal-mask.show');
      if (m) { m.remove(); return; }
    }
  });
});
