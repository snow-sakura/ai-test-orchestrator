from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import json
import os
import asyncio
import uuid

app = FastAPI(title="AI Test Orchestrator Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_FILE = os.path.join(os.path.dirname(__file__), "workflows.json")
RUNS_FILE = os.path.join(os.path.dirname(__file__), "runs.json")
ASSETS_FILE = os.path.join(os.path.dirname(__file__), "assets.json")
TASKS_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")
AUDIT_FILE = os.path.join(os.path.dirname(__file__), "audit.json")
CAPABILITIES_FILE = os.path.join(os.path.dirname(__file__), "capabilities.json")
RESOURCES_FILE = os.path.join(os.path.dirname(__file__), "resources.json")

TASK_TYPES = ["异步测试任务", "回归任务", "探索任务", "外部智能体任务", "数据生成任务"]
TASK_TYPE_LABELS = {
    "异步测试任务": "异步测试任务",
    "回归任务": "回归任务",
    "探索任务": "探索任务",
    "外部智能体任务": "外部智能体任务",
    "数据生成任务": "数据生成任务",
}
TASK_STATUS_LABELS = {
    "running": "运行中",
    "success": "已完成",
    "failed": "失败",
    "timeout": "超时",
    "canceled": "已取消",
}


# ============ Pydantic 模型 ============
class NodeConfig(BaseModel):
    model_config = {"extra": "allow"}
    id: str
    label: str
    type: str
    position: Dict[str, float]
    data: Optional[Dict] = {}
    config: Optional[Dict] = {}


class EdgeConfig(BaseModel):
    id: str
    source: str
    target: str


class Workflow(BaseModel):
    id: str
    name: str
    nodes: List[NodeConfig]
    edges: List[EdgeConfig]


# ============ 持久化 ============
def load_storage() -> Dict[str, Any]:
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_storage(data: Dict[str, Any]):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 内存存储执行状态
execution_registry: Dict[str, Dict[str, Any]] = {}


def load_runs() -> Dict[str, Any]:
    if os.path.exists(RUNS_FILE):
        with open(RUNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_runs(data: Dict[str, Any]):
    with open(RUNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def load_assets() -> Dict[str, Any]:
    if os.path.exists(ASSETS_FILE):
        with open(ASSETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_assets(data: Dict[str, Any]):
    with open(ASSETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_tasks() -> Dict[str, Any]:
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_tasks(data: Dict[str, Any]):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


ASSET_TYPES = ["用例", "脚本", "数据模板", "能力包", "变更驱动用例"]
ASSET_TYPE_LABELS = {
    "用例": "认证用例",
    "脚本": "认证自动化脚本",
    "数据模板": "认证测试数据模板",
    "能力包": "认证能力包",
    "变更驱动用例": "代码变更驱动的生成用例",
}
ASSET_STATUS_LABELS = {
    "certified": "已认证",
    "pending": "待认证",
    "rejected": "未通过",
    "retired": "已退役",
}


def seed_assets():
    """V5：预置示例认证资产"""
    assets = load_assets()
    if assets:
        return
    seeds = [
        {"id": "asset_case_001", "type": "用例", "name": "移动端登录全流程认证用例", "version": 3, "status": "certified",
         "scope": ["移动端", "iOS", "Android"], "quality": {"mutationScore": 0.92, "stability": 0.95, "regressionResult": "pass"},
         "references": ["wf_cicd", "wf_mobile"], "certifiedAt": "2026-09-15", "retireAlert": False,
         "auditLog": [{"ts": "2026-09-15", "action": "certified", "by": "质量门禁节点", "detail": "通过全部质量门槛"}]},
        {"id": "asset_script_001", "type": "脚本", "name": "API 接口巡检自动化脚本", "version": 1, "status": "certified",
         "scope": ["API", "巡检"], "quality": {"mutationScore": 0.88, "stability": 0.97, "regressionResult": "pass"},
         "references": ["wf_api_daily"], "certifiedAt": "2026-10-01", "retireAlert": False,
         "auditLog": [{"ts": "2026-10-01", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}]},
        {"id": "asset_data_001", "type": "数据模板", "name": "用户角色权限测试数据模板", "version": 2, "status": "certified",
         "scope": ["权限", "RBAC"], "quality": {"mutationScore": 0.90, "stability": 0.93, "regressionResult": "pass"},
         "references": [], "certifiedAt": "2026-08-20", "retireAlert": False,
         "auditLog": [{"ts": "2026-08-20", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}]},
        {"id": "asset_skill_001", "type": "能力包", "name": "Browser-use 浏览器智能体能力包", "version": 5, "status": "certified",
         "scope": ["Web", "UI", "探索"], "quality": {"mutationScore": 0.85, "stability": 0.91, "regressionResult": "pass"},
         "references": ["wf_explore"], "certifiedAt": "2026-10-10", "retireAlert": False,
         "auditLog": [{"ts": "2026-10-10", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}]},
        {"id": "asset_cd_001", "type": "变更驱动用例", "name": "支付模块变更驱动回归用例集", "version": 1, "status": "pending",
         "scope": ["支付", "回归"], "quality": {"mutationScore": 0.72, "stability": 0.60, "regressionResult": "pending"},
         "references": [], "certifiedAt": "", "retireAlert": False,
         "auditLog": [{"ts": "2026-10-25", "action": "created", "by": "代码变更驱动测试生成节点", "detail": "生成待认证"}]},
        {"id": "asset_case_002", "type": "用例", "name": "旧版订单流程用例（已失效）", "version": 4, "status": "retired",
         "scope": ["订单", "旧版"], "quality": {"mutationScore": 0.55, "stability": 0.40, "regressionResult": "fail"},
         "references": ["wf_order_old"], "certifiedAt": "2026-05-01", "retireAlert": True,
         "auditLog": [
             {"ts": "2026-05-01", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"},
             {"ts": "2026-10-20", "action": "retired", "by": "平台", "detail": "被测系统订单模块重大变更，资产可能失效"}]},
    ]
    for s in seeds:
        assets[s["id"]] = s
    save_assets(assets)


def seed_tasks():
    """V6：预置异步任务看板数据（PRD §6.4：运行中 / 已完成 / 失败 / 超时 四态齐全）"""
    tasks = load_tasks()
    if tasks:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    seeds = [
        # 运行中：异步测试任务（轮询模式）
        {
            "id": "task_running_001",
            "type": "异步测试任务",
            "name": "支付模块异步回归测试任务",
            "status": "running",
            "workflow": "wf_payment_regression",
            "node": "n_async_regression",
            "progress": 62,
            "started": "2026-10-26 14:02",
            "eta": "约 8 分钟",
            "owner": "test-agent-01",
            "resource": "browser-farm-A",
            "result_ref": "var://wf_payment_regression/result_async",
            "poll_interval": 15,
            "timeout_sec": 1800,
            "mode": "poll",
            "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 14:02", "action": "submitted", "by": "异步测试执行节点", "detail": "任务已提交，立即返回任务标识"},
                {"ts": "2026-10-26 14:35", "action": "polling", "by": "平台", "detail": f"第 {now} 轮轮询，进度 62%"},
            ],
            "created": now,
        },
        # 运行中：外部智能体任务（回调模式）
        {
            "id": "task_running_002",
            "type": "外部智能体任务",
            "name": "Browser-use 智能探索外部调用",
            "status": "running",
            "workflow": "wf_explore",
            "node": "n_external_agent",
            "progress": 38,
            "started": "2026-10-26 13:48",
            "eta": "约 15 分钟",
            "owner": "external-agent-7",
            "resource": "web-farm-B",
            "result_ref": "var://wf_explore/external_result",
            "poll_interval": 0,
            "timeout_sec": 3600,
            "mode": "callback",
            "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 13:48", "action": "submitted", "by": "外部智能体节点", "detail": "已提交外部调用，等待事件回调"},
                {"ts": "2026-10-26 14:00", "action": "callback", "by": "external-agent-7", "detail": "回调事件已接收，进度 38%"},
            ],
            "created": now,
        },
        # 已完成
        {
            "id": "task_success_001",
            "type": "回归任务",
            "name": "核心接口每日巡检回归任务",
            "status": "success",
            "workflow": "wf_api_daily",
            "node": "n_regression",
            "progress": 100,
            "started": "2026-10-26 09:00",
            "eta": "已完成",
            "owner": "test-agent-02",
            "resource": "api-farm-C",
            "result_ref": "var://wf_api_daily/regression_result",
            "poll_interval": 30,
            "timeout_sec": 900,
            "mode": "poll",
            "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 09:00", "action": "submitted", "by": "回归任务节点", "detail": "任务已提交"},
                {"ts": "2026-10-26 09:12", "action": "completed", "by": "平台", "detail": "结果已写回变量池 var://wf_api_daily/regression_result，唤醒下游节点"},
            ],
            "created": now,
        },
        # 失败
        {
            "id": "task_failed_001",
            "type": "数据生成任务",
            "name": "用户角色权限测试数据生成",
            "status": "failed",
            "workflow": "wf_rbac",
            "node": "n_data_gen",
            "progress": 45,
            "started": "2026-10-26 10:15",
            "eta": "失败",
            "owner": "data-agent-1",
            "resource": "data-farm-D",
            "result_ref": "var://wf_rbac/data_result",
            "poll_interval": 20,
            "timeout_sec": 600,
            "mode": "poll",
            "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 10:15", "action": "submitted", "by": "数据生成节点", "detail": "任务已提交"},
                {"ts": "2026-10-26 10:24", "action": "failed", "by": "data-agent-1", "detail": "数据源连接超时，任务失败，未回写结果"},
            ],
            "created": now,
        },
        # 超时
        {
            "id": "task_timeout_001",
            "type": "探索任务",
            "name": "Web 端深度探索任务（已超时）",
            "status": "timeout",
            "workflow": "wf_web_explore",
            "node": "n_explore_deep",
            "progress": 71,
            "started": "2026-10-25 22:10",
            "eta": "已超时",
            "owner": "explore-agent-3",
            "resource": "browser-farm-E",
            "result_ref": "var://wf_web_explore/explore_result",
            "poll_interval": 30,
            "timeout_sec": 900,
            "mode": "poll",
            "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-25 22:10", "action": "submitted", "by": "探索任务节点", "detail": "任务已提交"},
                {"ts": "2026-10-25 22:25", "action": "timeout", "by": "平台", "detail": "超过最大执行时长（900s），按策略终止，未回写结果，转人工处理"},
            ],
            "created": now,
        },
        # 已取消
        {
            "id": "task_canceled_001",
            "type": "异步测试任务",
            "name": "移动端多端回归（已取消）",
            "status": "canceled",
            "workflow": "wf_mobile",
            "node": "n_mobile_async",
            "progress": 20,
            "started": "2026-10-25 18:30",
            "eta": "已取消",
            "owner": "test-agent-05",
            "resource": "device-farm-F",
            "result_ref": "var://wf_mobile/mobile_result",
            "poll_interval": 10,
            "timeout_sec": 1200,
            "mode": "poll",
            "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-25 18:30", "action": "submitted", "by": "移动端异步节点", "detail": "任务已提交"},
                {"ts": "2026-10-25 18:42", "action": "canceled", "by": "测试负责人", "detail": "手动取消任务，资源锁已释放"},
            ],
            "created": now,
        },
    ]
    for s in seeds:
        tasks[s["id"]] = s
    save_tasks(tasks)


def seed_runs():
    """V4：预置示例运行记录，保证 /runs 页面有可追溯的节点级时间线"""
    runs = load_runs()
    if runs:
        return
    default = {
        "id": "default-workflow",
        "name": "我的第一个测试工作流",
        "nodes": [
            {"id": "n1", "label": "开始"},
            {"id": "n2", "label": "需求解析"},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
        ],
    }
    run_id = "run_seed_001"
    t0 = now_str()
    runs[run_id] = {
        "id": run_id,
        "workflow_id": "default-workflow",
        "workflow_name": "我的第一个测试工作流",
        "trigger": "手动",
        "status": "completed",
        "started": "10-26 16:42:00",
        "duration": "2s08ms",
        "tokens": 1612,
        "cost": 0.0081,
        "gate": {"verdict": "通过", "engine": "确定性规则引擎", "narrative": "主要贡献因素为执行通过率与覆盖率"},
        "node_states": {"n1": "success", "n2": "success"},
        "timeline": [
            {
                "seq": 1, "nodeId": "n1", "label": "开始", "status": "success",
                "started": "16:42:01", "duration": "0.8s", "tokens": 806, "cost": 0.004,
                "model": "Claude-Opus-4.5",
                "input": {"source": "manual", "payload": {"caseId": "TC-2026-1026"}},
                "reasoning": "工作流入口节点，初始化执行上下文并装载触发参数。",
                "tools": [],
                "output": {"context": {"workflow": "default-workflow", "trigger": "手动"}},
                "evidence": ["trace:n1"],
            },
            {
                "seq": 2, "nodeId": "n2", "label": "需求解析", "status": "success",
                "started": "16:42:02", "duration": "1.2s", "tokens": 806, "cost": 0.0041,
                "model": "Gemini-2.5-Pro",
                "input": {"binding": "$.n1.context", "payload": {"requirement": "移动端多端回归需求"}},
                "reasoning": "抽取 3 个可测需求点，1 个隐含边界条件（弱网超时重试）。",
                "tools": ["webFetch"],
                "output": {"requirementPoints": 3, "ambiguities": 0},
                "evidence": ["log:n2:001", "trace:n2"],
            },
        ],
        "logs": [
            {"nodeId": "n1", "msg": "节点「开始」开始执行（模型 Claude-Opus-4.5）", "time": "16:42:01"},
            {"nodeId": "n1", "msg": "节点「开始」执行成功 · Token 806 · 成本 ¥0.0040", "time": "16:42:02"},
            {"nodeId": "n2", "msg": "节点「需求解析」开始执行（模型 Gemini-2.5-Pro）", "time": "16:42:02"},
            {"nodeId": "n2", "msg": "工具调用: webFetch", "time": "16:42:03"},
            {"nodeId": "n2", "msg": "节点「需求解析」执行成功 · Token 806 · 成本 ¥0.0041", "time": "16:42:03"},
            {"nodeId": "global", "msg": "工作流执行完毕 · 总 Token 1612 · 总成本 ¥0.0081", "time": "16:42:04"},
        ],
        "created": t0,
    }
    save_runs(runs)


# ============ 基础接口 ============
@app.get("/")
async def root():
    return {"message": "AI Test Orchestrator Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ============ 工作台总览（V1） ============
@app.get("/dashboard/summary")
async def dashboard_summary():
    storage = load_storage()
    kpis = [
        {"label": "工作流总数", "value": str(len(storage)) if storage else "8", "icon": "📋", "trend": 14},
        {"label": "今日运行", "value": "42", "icon": "▶", "trend": 8},
        {"label": "通过率", "value": "91%", "icon": "✅", "trend": 3},
        {"label": "本月成本", "value": "¥2,380", "icon": "💸", "trend": -6},
    ]
    recent_runs = [
        {"id": "r1", "wfName": "代码变更驱动的 CI/CD 质量门禁", "status": "success", "trigger": "Git Push", "started": "10-26 16:42", "dur": "6m18s", "cost": 4.82, "gate": "有条件通过"},
        {"id": "r2", "wfName": "核心接口每日巡检", "status": "success", "trigger": "定时", "started": "10-26 09:00", "dur": "2m05s", "cost": 1.20, "gate": "通过"},
        {"id": "r3", "wfName": "移动端多端回归", "status": "failed", "trigger": "手动", "started": "10-25 21:33", "dur": "4m40s", "cost": 3.10, "gate": "阻断"},
        {"id": "r4", "wfName": "安全基线扫描流水线", "status": "running", "trigger": "Git Push", "started": "10-25 15:20", "dur": "进行中", "cost": 0.85, "gate": ""},
    ]
    todos = [
        {"id": "t1", "icon": "✋", "title": "人工审批门", "detail": "工作流 wf_cicd · 高风险变更", "route": "/runs"},
        {"id": "t2", "icon": "📮", "title": "缺陷归档确认", "detail": "3 条待确认缺陷", "route": "/assets"},
        {"id": "t3", "icon": "🔑", "title": "能力接入审批", "detail": "2 项外部调用待审批", "route": "/capabilities"},
    ]
    paradigms = [
        {"id": "cicd", "name": "CI/CD 质量门禁", "icon": "🚦", "desc": "变更→执行→门禁"},
        {"id": "explore", "name": "智能探索回归", "icon": "🕵️", "desc": "浏览器智能体+异步"},
        {"id": "mobile", "name": "移动端多端回归", "icon": "📱", "desc": "设备并行+资源锁"},
        {"id": "design", "name": "需求到用例", "icon": "🧩", "desc": "解析→生成→认证"},
        {"id": "external", "name": "外部智能体按需", "icon": "🌐", "desc": "鉴权→触发→回调"},
    ]
    return {
        "kpis": kpis,
        "recentRuns": recent_runs,
        "todos": todos,
        "paradigms": paradigms,
        "pendingCount": 5,
        "runningCount": 2,
    }


# ============ 工作流列表增强（V2：模型与模板常量） ============
class WorkflowNew(BaseModel):
    id: Optional[str] = None
    name: str
    status: str = "draft"
    template: Optional[str] = None


class WorkflowRename(BaseModel):
    name: str


class WorkflowPublish(BaseModel):
    status: str = "published"


PARADIGM_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "cicd": {
        "name": "代码变更驱动的 CI/CD 质量门禁",
        "nodes": [
            {"id": "start", "label": "开始", "type": "platform", "position": {"x": 40, "y": 120}},
            {"id": "impact", "label": "变更影响分析", "type": "analysis", "position": {"x": 220, "y": 120}},
            {"id": "risk", "label": "风险评级", "type": "analysis", "position": {"x": 400, "y": 120}},
            {"id": "gen", "label": "代码变更驱动测试生成", "type": "analysis", "position": {"x": 580, "y": 120}},
            {"id": "gate", "label": "质量门禁", "type": "decision", "position": {"x": 760, "y": 120}},
            {"id": "report", "label": "测试报告生成", "type": "decision", "position": {"x": 940, "y": 120}},
            {"id": "end", "label": "结束", "type": "platform", "position": {"x": 1120, "y": 120}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "impact"},
            {"id": "e2", "source": "impact", "target": "risk"},
            {"id": "e3", "source": "risk", "target": "gen"},
            {"id": "e4", "source": "gen", "target": "gate"},
            {"id": "e5", "source": "gate", "target": "report"},
            {"id": "e6", "source": "report", "target": "end"},
        ],
    },
    "explore": {
        "name": "智能探索与大规模异步回归",
        "nodes": [
            {"id": "start", "label": "开始", "type": "platform", "position": {"x": 40, "y": 120}},
            {"id": "strategy", "label": "测试策略生成", "type": "analysis", "position": {"x": 240, "y": 120}},
            {"id": "browser", "label": "智能浏览器自动化", "type": "execution", "position": {"x": 440, "y": 60}},
            {"id": "async", "label": "异步任务提交与轮询", "type": "control", "position": {"x": 440, "y": 180}},
            {"id": "triage", "label": "失败分诊", "type": "diagnosis", "position": {"x": 640, "y": 120}},
            {"id": "gate", "label": "质量门禁", "type": "decision", "position": {"x": 840, "y": 120}},
            {"id": "end", "label": "结束", "type": "platform", "position": {"x": 1040, "y": 120}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "strategy"},
            {"id": "e2", "source": "strategy", "target": "browser"},
            {"id": "e3", "source": "strategy", "target": "async"},
            {"id": "e4", "source": "browser", "target": "triage"},
            {"id": "e5", "source": "async", "target": "triage"},
            {"id": "e6", "source": "triage", "target": "gate"},
            {"id": "e7", "source": "gate", "target": "end"},
        ],
    },
    "mobile": {
        "name": "移动端多端回归",
        "nodes": [
            {"id": "start", "label": "开始", "type": "platform", "position": {"x": 40, "y": 120}},
            {"id": "strategy", "label": "测试策略生成", "type": "analysis", "position": {"x": 240, "y": 120}},
            {"id": "devA", "label": "移动端图像识别（设备A）", "type": "execution", "position": {"x": 440, "y": 40}},
            {"id": "devB", "label": "移动端图像识别（设备B）", "type": "execution", "position": {"x": 440, "y": 140}},
            {"id": "web", "label": "Web UI 执行", "type": "execution", "position": {"x": 440, "y": 240}},
            {"id": "diff", "label": "兼容性差异比对", "type": "diagnosis", "position": {"x": 660, "y": 140}},
            {"id": "triage", "label": "失败分诊", "type": "diagnosis", "position": {"x": 860, "y": 140}},
            {"id": "end", "label": "结束", "type": "platform", "position": {"x": 1060, "y": 140}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "strategy"},
            {"id": "e2", "source": "strategy", "target": "devA"},
            {"id": "e3", "source": "strategy", "target": "devB"},
            {"id": "e4", "source": "strategy", "target": "web"},
            {"id": "e5", "source": "devA", "target": "diff"},
            {"id": "e6", "source": "devB", "target": "diff"},
            {"id": "e7", "source": "web", "target": "diff"},
            {"id": "e8", "source": "diff", "target": "triage"},
            {"id": "e9", "source": "triage", "target": "end"},
        ],
    },
    "design": {
        "name": "需求到用例的测试设计流水线",
        "nodes": [
            {"id": "start", "label": "开始", "type": "platform", "position": {"x": 40, "y": 120}},
            {"id": "req", "label": "需求解析", "type": "analysis", "position": {"x": 240, "y": 120}},
            {"id": "case", "label": "测试用例生成", "type": "analysis", "position": {"x": 440, "y": 120}},
            {"id": "data", "label": "测试数据合成", "type": "analysis", "position": {"x": 640, "y": 120}},
            {"id": "cov", "label": "测试充分性评估", "type": "decision", "position": {"x": 840, "y": 120}},
            {"id": "cert", "label": "测试资产认证", "type": "decision", "position": {"x": 1040, "y": 120}},
            {"id": "end", "label": "结束", "type": "platform", "position": {"x": 1240, "y": 120}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "req"},
            {"id": "e2", "source": "req", "target": "case"},
            {"id": "e3", "source": "case", "target": "data"},
            {"id": "e4", "source": "data", "target": "cov"},
            {"id": "e5", "source": "cov", "target": "cert"},
            {"id": "e6", "source": "cert", "target": "end"},
        ],
    },
    "external": {
        "name": "外部智能体触发按需测试",
        "nodes": [
            {"id": "start", "label": "开始（外部调用）", "type": "platform", "position": {"x": 40, "y": 120}},
            {"id": "auth", "label": "鉴权与审批", "type": "platform", "position": {"x": 240, "y": 120}},
            {"id": "exec", "label": "指定工作流执行", "type": "execution", "position": {"x": 440, "y": 120}},
            {"id": "async", "label": "异步任务提交与轮询", "type": "control", "position": {"x": 640, "y": 120}},
            {"id": "cb", "label": "结果回调", "type": "platform", "position": {"x": 840, "y": 120}},
            {"id": "end", "label": "结束", "type": "platform", "position": {"x": 1040, "y": 120}},
        ],
        "edges": [
            {"id": "e1", "source": "start", "target": "auth"},
            {"id": "e2", "source": "auth", "target": "exec"},
            {"id": "e3", "source": "exec", "target": "async"},
            {"id": "e4", "source": "async", "target": "cb"},
            {"id": "e5", "source": "cb", "target": "end"},
        ],
    },
}


# ============ 工作流 CRUD ============
@app.get("/workflows/templates")
async def list_templates():
    return [
        {"id": k, "name": v["name"]} for k, v in PARADIGM_TEMPLATES.items()
    ]


@app.post("/workflows/new")
async def create_workflow(payload: WorkflowNew):
    storage = load_storage()
    wf_id = payload.id or f"wf_{uuid.uuid4().hex[:8]}"
    if payload.template and payload.template in PARADIGM_TEMPLATES:
        tpl = PARADIGM_TEMPLATES[payload.template]
        nodes = [
            {**n, "config": n.get("config", {})} for n in tpl["nodes"]
        ]
        edges = tpl["edges"]
        name = payload.name or tpl["name"]
    else:
        nodes = [
            {"id": "start", "label": "开始", "type": "platform", "position": {"x": 80, "y": 120}, "config": {}},
            {"id": "end", "label": "结束", "type": "platform", "position": {"x": 480, "y": 120}, "config": {}},
        ]
        edges = [{"id": "e1", "source": "start", "target": "end"}]
        name = payload.name or "未命名工作流"
    storage[wf_id] = {
        "id": wf_id,
        "name": name,
        "status": payload.status,
        "template": payload.template,
        "nodes": nodes,
        "edges": edges,
    }
    save_storage(storage)
    return {"status": "success", "id": wf_id, "name": name}


@app.get("/workflows")
async def list_workflows():
    storage = load_storage()
    return list(storage.values())


@app.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    storage = load_storage()
    if workflow_id not in storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return storage[workflow_id]


@app.post("/workflows")
async def save_workflow(workflow: Workflow):
    storage = load_storage()
    storage[workflow.id] = workflow.model_dump()
    save_storage(storage)
    return {"status": "success", "id": workflow.id}


@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    storage = load_storage()
    if workflow_id not in storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    del storage[workflow_id]
    save_storage(storage)
    return {"status": "success"}


@app.post("/workflows/{workflow_id}/rename")
async def rename_workflow(workflow_id: str, payload: WorkflowRename):
    storage = load_storage()
    if workflow_id not in storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    storage[workflow_id]["name"] = payload.name
    save_storage(storage)
    return {"status": "success"}


@app.post("/workflows/{workflow_id}/publish")
async def publish_workflow(workflow_id: str, payload: WorkflowPublish):
    storage = load_storage()
    if workflow_id not in storage:
        raise HTTPException(status_code=404, detail="Workflow not found")
    storage[workflow_id]["status"] = payload.status
    save_storage(storage)
    return {"status": "success", "id": workflow_id, "wfStatus": payload.status}


# ============ 执行引擎 ============
@app.on_event("startup")
async def _startup_seed():
    seed_runs()
    seed_assets()
    seed_tasks()
    seed_models()
    seed_audit()
    seed_capabilities()
    seed_resources()
    seed_settings()


@app.post("/execute/{workflow_id}")
async def execute_workflow(workflow_id: str):
    storage = load_storage()
    if workflow_id not in storage:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow = storage[workflow_id]
    exec_id = str(uuid.uuid4())

    node_states = {node["id"]: "pending" for node in workflow["nodes"]}
    execution_registry[exec_id] = {
        "workflow_id": workflow_id,
        "workflow_name": workflow.get("name", workflow_id),
        "status": "running",
        "trigger": "手动",
        "started": now_str(),
        "node_states": node_states,
        "logs": [],
        "timeline": [],
    }

    asyncio.create_task(run_execution_engine(exec_id, workflow))
    return {"execution_id": exec_id}


@app.get("/execution/{exec_id}")
async def get_execution_status(exec_id: str):
    if exec_id not in execution_registry:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution_registry[exec_id]


# ============ 执行追踪（V4） ============
@app.get("/runs")
async def list_runs():
    """返回所有运行记录（含预置示例 + 已执行），按时间倒序"""
    runs = load_runs()
    items = list(runs.values())
    # 加入当前正在 running 的（内存中未持久化的）
    for exec_id, reg in execution_registry.items():
        if reg["status"] == "running" and exec_id not in runs:
            items.append({
                "id": exec_id,
                "workflow_id": reg.get("workflow_id", ""),
                "workflow_name": reg.get("workflow_name", ""),
                "trigger": reg.get("trigger", "手动"),
                "status": "running",
                "started": reg.get("started", ""),
                "duration": "进行中",
                "tokens": 0,
                "cost": 0.0,
                "gate": None,
                "node_states": reg.get("node_states", {}),
                "timeline": reg.get("timeline", []),
                "logs": reg.get("logs", []),
            })
    items.sort(key=lambda r: r.get("created", r.get("started", "")), reverse=True)
    return items


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    """返回单条运行详情（含节点级时间线 + 门禁裁决）"""
    runs = load_runs()
    if run_id in runs:
        return runs[run_id]
    if run_id in execution_registry:
        return execution_registry[run_id]
    raise HTTPException(status_code=404, detail="Run not found")


# ============ 认证资产库（V5） ============
class AssetNew(BaseModel):
    model_config = {"extra": "allow"}
    name: str
    type: str
    version: int = 1
    scope: List[str] = []


class AssetRetire(BaseModel):
    reason: str = "被测系统发生重大变更，资产可能失效"


class AssetReference(BaseModel):
    workflow: str
    version: Optional[int] = None


def _with_asset_meta(assets: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    for raw in assets.values():
        item = dict(raw)
        item["typeLabel"] = ASSET_TYPE_LABELS.get(item.get("type", ""), item.get("type", ""))
        item["statusLabel"] = ASSET_STATUS_LABELS.get(item.get("status", ""), item.get("status", ""))
        items.append(_certify_by_rules(item))
    return items


def _append_asset_audit(a: Dict[str, Any], action: str, by: str, detail: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    a.setdefault("auditLog", []).append({"ts": now, "action": action, "by": by, "detail": detail})


def _certify_by_rules(a: Dict[str, Any]) -> Dict[str, Any]:
    q = a.get("quality", {})
    checks = [
        {"key": "mutationScore", "label": "变异分数", "value": q.get("mutationScore", 0), "passed": q.get("mutationScore", 0) >= 0.8, "threshold": "≥ 0.80"},
        {"key": "stability", "label": "稳定性", "value": q.get("stability", 0), "passed": q.get("stability", 0) >= 0.8, "threshold": "≥ 0.80"},
        {"key": "regressionResult", "label": "副作用回归结果", "value": q.get("regressionResult", "pending"), "passed": q.get("regressionResult") == "pass", "threshold": "必须通过"},
    ]
    passed = all(c["passed"] for c in checks)
    a["qualityChecks"] = checks
    a["qualityGate"] = "通过" if passed else "未通过"
    return a


@app.get("/assets/meta")
async def asset_meta():
    return {
        "types": ASSET_TYPES,
        "typeLabels": ASSET_TYPE_LABELS,
        "statusLabels": ASSET_STATUS_LABELS,
        "qualityGate": "变异分数 / 稳定性 / 副作用回归三项门槛由平台规则引擎判定，认证状态变更写入审计日志。",
    }


@app.get("/assets")
async def list_assets():
    return _with_asset_meta(load_assets())


@app.post("/assets")
async def create_asset(payload: AssetNew):
    if payload.type not in ASSET_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported asset type")
    assets = load_assets()
    aid = f"asset_{payload.type}_{uuid.uuid4().hex[:8]}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new = {
        "id": aid,
        "type": payload.type,
        "name": payload.name,
        "version": payload.version,
        "status": "pending",
        "scope": payload.scope,
        "quality": {"mutationScore": 0.0, "stability": 0.0, "regressionResult": "pending"},
        "references": [],
        "pinnedVersions": {},
        "certifiedAt": "",
        "retireAlert": False,
        "auditLog": [{"ts": now, "action": "created", "by": "认证资产库", "detail": "新建资产待认证"}],
    }
    new = _certify_by_rules(new)
    assets[aid] = new
    save_assets(assets)
    return {"status": "success", "id": aid, "asset": _with_asset_meta({aid: new})[0]}


@app.get("/assets/search")
async def search_assets(q: str = "", type: str = "", scope: str = "", status: str = ""):
    items = list(load_assets().values())
    q = q.strip().lower()
    if q:
        items = [a for a in items if q in a.get("name", "").lower()]
    if type:
        items = [a for a in items if a.get("type") == type]
    if scope:
        items = [a for a in items if scope in a.get("scope", [])]
    if status:
        items = [a for a in items if a.get("status") == status]
    return _with_asset_meta({a["id"]: a for a in items})


@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    assets = load_assets()
    if asset_id not in assets:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _with_asset_meta({asset_id: _certify_by_rules(assets[asset_id])})[asset_id]


@app.post("/assets/{asset_id}/certify")
async def certify_asset(asset_id: str):
    assets = load_assets()
    if asset_id not in assets:
        raise HTTPException(status_code=404, detail="Asset not found")
    a = assets[asset_id]
    a = _certify_by_rules(a)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    if a.get("qualityGate") == "通过":
        a["status"] = "certified"
        a["certifiedAt"] = now
        a["version"] = a.get("version", 1) + 1
        a["retireAlert"] = False
        _append_asset_audit(a, "certified", "测试资产认证节点", f"通过质量门槛，升级为认证资产（v{a['version']}）")
    else:
        a["status"] = "rejected"
        _append_asset_audit(a, "rejected", "测试资产认证节点", "未通过质量门槛（变异分数/稳定性/副作用回归）")
    assets[asset_id] = a
    save_assets(assets)
    return {"status": "success", "asset": _with_asset_meta({asset_id: a})[0]}


@app.post("/assets/{asset_id}/retire")
async def retire_asset(asset_id: str, payload: AssetRetire):
    assets = load_assets()
    if asset_id not in assets:
        raise HTTPException(status_code=404, detail="Asset not found")
    a = assets[asset_id]
    a["status"] = "retired"
    a["retireAlert"] = True
    _append_asset_audit(a, "retired", "平台", payload.reason or "资产退役")
    assets[asset_id] = a
    save_assets(assets)
    return {"status": "success", "asset": _with_asset_meta({asset_id: a})[0]}


@app.post("/assets/{asset_id}/reference")
async def reference_asset(asset_id: str, payload: AssetReference):
    assets = load_assets()
    if asset_id not in assets:
        raise HTTPException(status_code=404, detail="Asset not found")
    a = assets[asset_id]
    version = payload.version or a.get("version", 1)
    if payload.workflow not in a.setdefault("references", []):
        a["references"].append(payload.workflow)
    a.setdefault("pinnedVersions", {})[payload.workflow] = version
    _append_asset_audit(a, "referenced", payload.workflow or "unknown", f"版本锁定 v{version}")
    assets[asset_id] = a
    save_assets(assets)
    return {"status": "success", "asset": _with_asset_meta({asset_id: a})[0]}


# ============ 异步任务看板（V6） ============
class TaskNew(BaseModel):
    model_config = {"extra": "allow"}
    name: str
    type: str
    workflow: str = ""
    node: str = ""
    resource: str = ""
    result_ref: str = ""
    poll_interval: int = 15
    timeout_sec: int = 3600
    mode: str = "poll"


class TaskStatusPayload(BaseModel):
    detail: str = ""


def _with_task_meta(task: Dict[str, Any]) -> Dict[str, Any]:
    task = dict(task)
    task["typeLabel"] = TASK_TYPE_LABELS.get(task.get("type", ""), task.get("type", ""))
    task["statusLabel"] = TASK_STATUS_LABELS.get(task.get("status", ""), task.get("status", ""))
    task["modeLabel"] = "轮询" if task.get("mode") == "poll" else "回调"
    task["progress"] = max(0, min(100, int(task.get("progress") or 0)))
    task["auditLog"] = task.get("auditLog", [])
    return task


def _append_task_audit(task: Dict[str, Any], action: str, by: str, detail: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    task.setdefault("auditLog", []).append({"ts": now, "action": action, "by": by, "detail": detail})


def _task_filter_items(tasks: Dict[str, Any], q: str = "", type_filter: str = "", status_filter: str = "", workflow: str = "", node: str = "", resource: str = "") -> List[Dict[str, Any]]:
    items = list(tasks.values())
    q = q.strip().lower()
    if q:
        items = [t for t in items if q in t.get("name", "").lower()]
    if type_filter:
        items = [t for t in items if t.get("type") == type_filter]
    if status_filter:
        items = [t for t in items if t.get("status") == status_filter]
    if workflow:
        items = [t for t in items if t.get("workflow") == workflow]
    if node:
        items = [t for t in items if t.get("node") == node]
    if resource:
        items = [t for t in items if t.get("resource") == resource]
    return items


@app.get("/tasks/meta")
async def task_meta():
    return {
        "types": TASK_TYPES,
        "typeLabels": TASK_TYPE_LABELS,
        "statusLabels": TASK_STATUS_LABELS,
        "statusBoard": ["running", "success", "failed", "timeout"],
    }


@app.get("/tasks")
async def list_tasks(q: str = "", type: str = "", status: str = "", workflow: str = "", node: str = "", resource: str = ""):
    items = _task_filter_items(load_tasks(), q, type, status, workflow, node, resource)
    return [_with_task_meta(t) for t in items]


@app.post("/tasks")
async def create_task(payload: TaskNew):
    if payload.type not in TASK_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported task type")
    tasks = load_tasks()
    tid = f"task_{uuid.uuid4().hex[:8]}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    task = {
        "id": tid,
        "type": payload.type,
        "name": payload.name,
        "status": "running",
        "workflow": payload.workflow,
        "node": payload.node,
        "progress": 0,
        "started": now,
        "eta": "计算中",
        "owner": "test-agent-new",
        "resource": payload.resource,
        "result_ref": payload.result_ref or f"var://{payload.workflow or tid}/result",
        "poll_interval": payload.poll_interval,
        "timeout_sec": payload.timeout_sec,
        "mode": payload.mode if payload.mode in ("poll", "callback") else "poll",
        "cancel_status": "idle",
        "auditLog": [
            {"ts": now, "action": "submitted", "by": "异步任务提交节点", "detail": "任务已提交，立即返回任务标识与结果获取引用"},
        ],
        "created": now,
    }
    task = _with_task_meta(task)
    tasks[tid] = task
    save_tasks(tasks)
    return {"status": "success", "id": tid, "task": task}


@app.get("/tasks/search")
async def search_tasks(q: str = "", type: str = "", status: str = "", workflow: str = "", node: str = "", resource: str = ""):
    items = _task_filter_items(load_tasks(), q, type, status, workflow, node, resource)
    return [_with_task_meta(t) for t in items]


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _with_task_meta(tasks[task_id])


@app.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, payload: TaskStatusPayload):
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    t = tasks[task_id]
    if t.get("status") in ("success", "failed", "timeout", "canceled"):
        raise HTTPException(status_code=400, detail="Task already finished")
    t["status"] = "canceled"
    t["eta"] = "已取消"
    t["cancel_status"] = "done"
    _append_task_audit(t, "canceled", "平台", payload.detail or "手动取消任务，资源锁已释放")
    tasks[task_id] = t
    save_tasks(tasks)
    return {"status": "success", "task": _with_task_meta(t)}


@app.post("/tasks/{task_id}/poll")
async def poll_task(task_id: str):
    """模拟轮询/回调推进任务进度：进度 +25，超时/失败类状态保持，完成后写回变量池（PRD §6.4 结果回写）"""
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    t = tasks[task_id]
    if t.get("status") in ("success", "failed", "timeout", "canceled"):
        return {"status": "success", "task": _with_task_meta(t), "changed": False}
    new_progress = min(100, int(t.get("progress", 0)) + 25)
    t["progress"] = new_progress
    if new_progress >= 100:
        t["status"] = "success"
        t["eta"] = "已完成"
        _append_task_audit(t, "completed", "平台", f"结果已写回变量池 {t.get('result_ref', '')}，唤醒下游节点")
    else:
        t["eta"] = "进行中"
        action = "polling" if t.get("mode") == "poll" else "callback"
        _append_task_audit(t, action, "平台", f"轮询/回调推进，进度 {new_progress}%")
    tasks[task_id] = t
    save_tasks(tasks)
    return {"status": "success", "task": _with_task_meta(t), "changed": True}


@app.post("/tasks/{task_id}/timeout")
async def timeout_task(task_id: str, payload: TaskStatusPayload):
    """模拟超时策略：达到最大执行时长，按策略终止或转人工处理（PRD §6.4 超时与取消）"""
    tasks = load_tasks()
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    t = tasks[task_id]
    if t.get("status") in ("success", "failed", "timeout", "canceled"):
        raise HTTPException(status_code=400, detail="Task already finished")
    t["status"] = "timeout"
    t["eta"] = "已超时"
    _append_task_audit(t, "timeout", "平台", payload.detail or f"超过最大执行时长（{t.get('timeout_sec', 3600)}s），按策略终止，转人工处理")
    tasks[task_id] = t
    save_tasks(tasks)
    return {"status": "success", "task": _with_task_meta(t)}


# ============ 模型配置与额度管理（V7） ============
MODELS_FILE = os.path.join(os.path.dirname(__file__), "models.json")

MODEL_REGISTRY = [
    {"id": "claude_opus_4_5", "name": "Claude-Opus-4.5", "vendor": "Anthropic", "kind": "文本", "tier": "高", "context": "200K", "dailyLimit": 500, "pricePerMIn": 15.0, "pricePerMOut": 75.0, "desc": "旗舰推理模型，适合复杂归因与用例生成"},
    {"id": "claude_sonnet_4_5", "name": "Claude-Sonnet-4.5", "vendor": "Anthropic", "kind": "文本", "tier": "中", "context": "200K", "dailyLimit": 2000, "pricePerMIn": 3.0, "pricePerMOut": 15.0, "desc": "均衡性能与成本，适合大部分节点执行"},
    {"id": "gemini_2_5_pro", "name": "Gemini-2.5-Pro", "vendor": "Google", "kind": "文本", "tier": "高", "context": "1M", "dailyLimit": 1000, "pricePerMIn": 1.25, "pricePerMOut": 10.0, "desc": "超长上下文，适合大规模日志分析"},
    {"id": "gpt_4o", "name": "GPT-4o", "vendor": "OpenAI", "kind": "多模态", "tier": "中", "context": "128K", "dailyLimit": 2000, "pricePerMIn": 2.5, "pricePerMOut": 10.0, "desc": "多模态理解，适合 UI 截图分析"},
    {"id": "qwen3_max", "name": "Qwen3-Max", "vendor": "Alibaba", "kind": "文本", "tier": "中", "context": "256K", "dailyLimit": 3000, "pricePerMIn": 1.5, "pricePerMOut": 4.5, "desc": "中文理解与代码生成强项"},
    {"id": "claude_opus_4_5_vision", "name": "Claude-Opus-4.5-Vision", "vendor": "Anthropic", "kind": "视觉", "tier": "高", "context": "200K", "dailyLimit": 200, "pricePerMIn": 15.0, "pricePerMOut": 75.0, "desc": "视觉理解，适合缺陷截图识别"},
]


def load_models() -> Dict[str, Any]:
    if os.path.exists(MODELS_FILE):
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_models(data: Dict[str, Any]):
    with open(MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def seed_models():
    """V7：预置模型注册表、配置、额度授予记录与用量（PRD §6.5）"""
    store = load_models()
    if store:
        return
    store["registry"] = MODEL_REGISTRY
    # 三层配置（PRD §6.5：全站级 / 个人级 / 角色级）
    store["configs"] = {
        "global": {"level": "全站", "textModel": "claude_sonnet_4_5", "visionModel": "claude_opus_4_5_vision", "params": {"temperature": 0.2, "maxTokens": 4096}, "keyMasked": "sk-ant-••••••••7f3a", "connected": True, "keyMaskedSource": "管理员"},
        "personal_test_lead": {"level": "个人", "owner": "测试负责人", "textModel": "qwen3_max", "visionModel": "gpt_4o", "params": {"temperature": 0.3, "maxTokens": 8192}, "keyMasked": "sk-alb-••••••••9c2d", "connected": True, "keyMaskedSource": "个人自带凭据"},
        "role_gate_judge": {"level": "角色", "owner": "质量门禁裁决节点", "textModel": "claude_opus_4_5", "visionModel": "", "params": {"temperature": 0.0, "maxTokens": 2048}, "keyMasked": "sk-ant-••••••••7f3a", "connected": True, "keyMaskedSource": "继承全站"},
        "role_case_generator": {"level": "角色", "owner": "用例生成节点", "textModel": "gemini_2_5_pro", "visionModel": "", "params": {"temperature": 0.4, "maxTokens": 16384}, "keyMasked": "sk-goo-••••••••4e1b", "connected": False, "keyMaskedSource": "角色独立凭据"},
    }
    # 额度授予记录（PRD §6.5：按自然日叠加额外使用次数，可叠加、可撤销，按账号查询）
    store["grants"] = [
        {"id": "grant_001", "account": "测试负责人", "model": "claude_sonnet_4_5", "date": "2026-10-26", "extraQuota": 500, "revoked": False, "by": "管理员", "ts": "2026-10-26 08:00"},
        {"id": "grant_002", "account": "测试负责人", "model": "claude_sonnet_4_5", "date": "2026-10-25", "extraQuota": 300, "revoked": False, "by": "管理员", "ts": "2026-10-25 08:00"},
        {"id": "grant_003", "account": "测试负责人", "model": "gemini_2_5_pro", "date": "2026-10-24", "extraQuota": 200, "revoked": True, "by": "管理员", "ts": "2026-10-24 08:00"},
    ]
    # 额度状态（当日已用 / 可用）
    store["quotas"] = [
        {"account": "测试负责人", "model": "claude_sonnet_4_5", "dailyLimit": 2000, "usedToday": 1240, "extraToday": 800, "renewed": False},
        {"account": "测试负责人", "model": "gemini_2_5_pro", "dailyLimit": 1000, "usedToday": 1000, "extraToday": 0, "renewed": True},
        {"account": "测试负责人", "model": "qwen3_max", "dailyLimit": 3000, "usedToday": 460, "extraToday": 0, "renewed": False},
    ]
    # 用量记录（PRD §6.5 计量与成本：节点与运行 Token 消耗）
    store["usage"] = [
        {"id": "u1", "model": "claude_sonnet_4_5", "workflow": "我的第一个测试工作流", "node": "需求解析", "tokens": 806, "cost": 0.0041, "ts": "2026-10-26 14:02"},
        {"id": "u2", "model": "claude_opus_4_5", "workflow": "我的第一个测试工作流", "node": "质量门禁", "tokens": 1220, "cost": 0.0915, "ts": "2026-10-26 14:03"},
        {"id": "u3", "model": "gemini_2_5_pro", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "变更影响分析", "tokens": 3480, "cost": 0.0592, "ts": "2026-10-26 09:01"},
    ]
    save_models(store)


def _model_by_id(model_id: str) -> Dict[str, Any]:
    for m in MODEL_REGISTRY:
        if m["id"] == model_id:
            return m
    return {"id": model_id, "name": model_id}


def _with_quota_meta(q: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(q)
    base = _model_by_id(q.get("model", ""))
    q["modelName"] = base.get("name", q.get("model", ""))
    limit = int(q.get("dailyLimit", 0))
    used = int(q.get("usedToday", 0))
    extra = int(q.get("extraToday", 0))
    q["available"] = max(0, limit + extra - used)
    q["dailyLimit"] = limit
    q["usedToday"] = used
    q["extraToday"] = extra
    q["usedRatio"] = min(100.0, round(used / max(1, limit + extra) * 100, 1))
    return q


class ConfigNew(BaseModel):
    model_config = {"extra": "allow"}
    level: str
    owner: str = ""
    textModel: str = ""
    visionModel: str = ""
    params: Optional[Dict] = {}
    keyMasked: str = ""


class GrantNew(BaseModel):
    account: str
    model: str
    extraQuota: int
    date: str = ""


class RenewQuota(BaseModel):
    model: str
    extraQuota: int
    date: str = ""


@app.get("/models/meta")
async def model_meta():
    return {
        "registry": MODEL_REGISTRY,
        "configLevels": ["全站", "个人", "角色"],
        "note": "密钥不明文落盘，仅保存掩码；额度按自然日叠加，可撤销；用量支持按工作流 / 节点 / 账号查看。",
    }


@app.get("/models/registry")
async def model_registry():
    return MODEL_REGISTRY


@app.get("/models/configs")
async def model_configs(level: str = "", owner: str = ""):
    store = load_models()
    items = list(store.get("configs", {}).values())
    if level:
        items = [c for c in items if c.get("level") == level]
    if owner:
        items = [c for c in items if owner in c.get("owner", "")]
    for c in items:
        c["textModelName"] = _model_by_id(c.get("textModel", "")).get("name", c.get("textModel", ""))
        c["visionModelName"] = _model_by_id(c.get("visionModel", "")).get("name", c.get("visionModel", "") or "—")
    return items


@app.post("/models/configs")
async def upsert_model_config(payload: ConfigNew):
    store = load_models()
    configs = store.setdefault("configs", {})
    key = payload.level.lower() if payload.level == "全站" else f"{payload.level.lower()}_{payload.owner or 'default'}"
    cfg = {
        "level": payload.level,
        "owner": payload.owner,
        "textModel": payload.textModel,
        "visionModel": payload.visionModel,
        "params": payload.params or {},
        "keyMasked": payload.keyMasked,
        "connected": False,
        "keyMaskedSource": payload.level,
    }
    text_name = _model_by_id(payload.textModel).get("name", payload.textModel)
    configs[key] = cfg
    save_models(store)
    cfg["textModelName"] = text_name
    cfg["visionModelName"] = _model_by_id(payload.visionModel).get("name", payload.visionModel or "—")
    return {"status": "success", "config": cfg}


@app.post("/models/configs/{config_key}/test")
async def test_model_config(config_key: str):
    """连接测试（PRD §6.5）：模拟探测模型端点可达性"""
    store = load_models()
    configs = store.get("configs", {})
    if config_key not in configs:
        raise HTTPException(status_code=404, detail="Config not found")
    cfg = configs[config_key]
    # 模拟：密钥掩码非空则连接成功
    ok = bool(cfg.get("keyMasked"))
    cfg["connected"] = ok
    cfg["lastTestAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_models(store)
    return {"status": "success" if ok else "failed", "config": cfg, "message": "模型端点连接正常" if ok else "密钥缺失，无法连接"}


@app.get("/models/grants")
async def model_grants(account: str = "", model: str = ""):
    store = load_models()
    items = store.get("grants", [])
    if account:
        items = [g for g in items if g.get("account") == account]
    if model:
        items = [g for g in items if g.get("model") == model]
    for g in items:
        g["modelName"] = _model_by_id(g.get("model", "")).get("name", g.get("model", ""))
    return items


@app.post("/models/grants")
async def grant_quota(payload: GrantNew):
    """额度授予：按自然日叠加额外使用次数（可叠加，PRD §6.5）"""
    store = load_models()
    grants = store.setdefault("grants", [])
    gid = f"grant_{uuid.uuid4().hex[:6]}"
    grant = {
        "id": gid,
        "account": payload.account,
        "model": payload.model,
        "date": payload.date or datetime.now().strftime("%Y-%m-%d"),
        "extraQuota": payload.extraQuota,
        "revoked": False,
        "by": "管理员",
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    grants.append(grant)
    # 同步叠加到当日额度
    base = _model_by_id(payload.model)
    quotas = store.setdefault("quotas", [])
    q = next((x for x in quotas if x.get("account") == payload.account and x.get("model") == payload.model), None)
    if q is None:
        quotas.append({"account": payload.account, "model": payload.model, "dailyLimit": base.get("dailyLimit", 1000), "usedToday": 0, "extraToday": 0, "renewed": False})
        q = quotas[-1]
    q["extraToday"] = int(q.get("extraToday", 0)) + payload.extraQuota
    save_models(store)
    grant["modelName"] = base.get("name", payload.model)
    return {"status": "success", "grant": grant}


@app.post("/models/grants/{grant_id}/revoke")
async def revoke_grant(grant_id: str):
    """撤销额度授予（PRD §6.5：可撤销）"""
    store = load_models()
    grants = store.get("grants", [])
    target = next((g for g in grants if g.get("id") == grant_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Grant not found")
    target["revoked"] = True
    target["revokedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_models(store)
    return {"status": "success", "grant": target}


@app.get("/models/quotas")
async def model_quotas(account: str = "", model: str = ""):
    store = load_models()
    items = store.get("quotas", [])
    if account:
        items = [q for q in items if q.get("account") == account]
    if model:
        items = [q for q in items if q.get("model") == model]
    return [_with_quota_meta(q) for q in items]


@app.post("/models/quotas/renew")
async def renew_quota(payload: RenewQuota):
    """叠加当日额外额度（PRD §6.5：支持按自然日叠加额外使用次数）"""
    store = load_models()
    quotas = store.setdefault("quotas", [])
    base = _model_by_id(payload.model)
    q = next((x for x in quotas if x.get("account") == "测试负责人" and x.get("model") == payload.model), None)
    if q is None:
        quotas.append({"account": "测试负责人", "model": payload.model, "dailyLimit": base.get("dailyLimit", 1000), "usedToday": 0, "extraToday": 0, "renewed": False})
        q = quotas[-1]
    q["extraToday"] = int(q.get("extraToday", 0)) + payload.extraQuota
    q["renewed"] = True
    save_models(store)
    return {"status": "success", "quota": _with_quota_meta(q)}


@app.get("/models/usage")
async def model_usage(workflow: str = "", node: str = "", model: str = ""):
    """计量与成本（PRD §6.5）：支持按工作流 / 节点 / 模型维度查看"""
    store = load_models()
    items = store.get("usage", [])
    if workflow:
        items = [u for u in items if u.get("workflow") == workflow]
    if node:
        items = [u for u in items if u.get("node") == node]
    if model:
        items = [u for u in items if u.get("model") == model]
    for u in items:
        u["modelName"] = _model_by_id(u.get("model", "")).get("name", u.get("model", ""))
    return items


# ============ 审计证据账本（V8） ============
import hashlib
import base64

AUDIT_EVENT_TYPES = ["工具调用", "白名单拒绝", "质量门禁裁决", "缺陷归档", "人工审批", "升级处理"]
AUDIT_TYPE_LABELS = {
    "工具调用": "工具调用",
    "白名单拒绝": "白名单拒绝",
    "质量门禁裁决": "质量门禁裁决",
    "缺陷归档": "缺陷归档",
    "人工审批": "人工审批",
    "升级处理": "升级处理",
}


def load_audit() -> List[Dict[str, Any]]:
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_audit(items: List[Dict[str, Any]]):
    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _audit_entry_hash(item: Dict[str, Any]) -> str:
    """计算账本条目的 SHA-256 哈希（不含 prevHash 和 hash 本身，用于验证内容未被篡改）"""
    payload = {k: v for k, v in item.items() if k not in ("prevHash", "hash")}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _with_audit_chain(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """为账本条目建立哈希链（PRD §6.6 不可篡改证据账本）"""
    prev = "0" * 64
    for i, item in enumerate(items):
        item = dict(item)
        item["prevHash"] = prev
        item["hash"] = _audit_entry_hash(item)
        prev = item["hash"]
        items[i] = item
    return items


def _verify_audit_chain(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """验证哈希链完整性，返回校验结果"""
    prev = "0" * 64
    broken_at = -1
    for i, item in enumerate(items):
        expected_prev = item.get("prevHash", "")
        if expected_prev != prev:
            broken_at = i
            break
        recomputed = _audit_entry_hash(item)
        if recomputed != item.get("hash", ""):
            broken_at = i
            break
        prev = item.get("hash", "")
    return {
        "verified": broken_at == -1,
        "brokenAt": broken_at,
        "lastHash": items[-1]["hash"] if items else "",
        "total": len(items),
    }


def seed_audit():
    """V8：预置不可篡改审计证据账本（PRD §6.6）"""
    items = load_audit()
    if items:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    seeds = [
        {"id": "ev_001", "ts": "2026-10-26 09:01", "type": "工具调用", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "变更影响分析", "actor": "gemini_2_5_pro", "detail": "调用 webFetch 获取 Git diff 摘要", "refId": "trace:run_seed_002:n2"},
        {"id": "ev_002", "ts": "2026-10-26 09:02", "type": "白名单拒绝", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "变更影响分析", "actor": "平台规则引擎", "detail": "拒绝调用 shell_exec（不在白名单内）", "refId": "whitelist:run_seed_002:n2"},
        {"id": "ev_003", "ts": "2026-10-26 09:03", "type": "质量门禁裁决", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "质量门禁", "actor": "确定性规则引擎", "detail": "裁决：通过（执行通过率 96%，覆盖率 82%）", "refId": "gate:run_seed_002:n5"},
        {"id": "ev_004", "ts": "2026-10-25 21:35", "type": "缺陷归档", "workflow": "移动端多端回归", "node": "失败分诊", "actor": "失败分诊节点", "detail": "归档缺陷 DEF-2026-0921（登录崩溃），关联证据 ev_004", "refId": "defect:DEF-2026-0921"},
        {"id": "ev_005", "ts": "2026-10-25 21:36", "type": "人工审批", "workflow": "移动端多端回归", "node": "人工审批门", "actor": "测试负责人", "detail": "批准高风险缺陷升级处理", "refId": "approval:DEF-2026-0921"},
        {"id": "ev_006", "ts": "2026-10-24 15:20", "type": "升级处理", "workflow": "Web 端深度探索", "node": "探索任务节点", "actor": "平台", "detail": "任务超时，升级转人工处理", "refId": "escalation:task_timeout_001"},
        {"id": "ev_007", "ts": "2026-10-26 14:03", "type": "工具调用", "workflow": "我的第一个测试工作流", "node": "需求解析", "actor": "claude_sonnet_4_5", "detail": "调用 webFetch 获取需求文档", "refId": "trace:run_seed_001:n2"},
    ]
    items = _with_audit_chain(seeds)
    save_audit(items)


class AuditNew(BaseModel):
    model_config = {"extra": "allow"}
    type: str
    workflow: str = ""
    node: str = ""
    actor: str = ""
    detail: str = ""
    refId: str = ""


@app.get("/audit/meta")
async def audit_meta():
    return {
        "types": AUDIT_EVENT_TYPES,
        "typeLabels": AUDIT_TYPE_LABELS,
        "note": "账本条目按时间顺序建立哈希链，任意条目被篡改后链校验即失败，满足合规审计要求（PRD §6.6）。",
    }


@app.get("/audit")
async def list_audit(type: str = "", workflow: str = "", node: str = "", refId: str = ""):
    items = load_audit()
    if type:
        items = [i for i in items if i.get("type") == type]
    if workflow:
        items = [i for i in items if i.get("workflow") == workflow]
    if node:
        items = [i for i in items if i.get("node") == node]
    if refId:
        items = [i for i in items if refId in i.get("refId", "")]
    return items


@app.post("/audit")
async def append_audit(payload: AuditNew):
    if payload.type not in AUDIT_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported audit event type")
    items = load_audit()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prev_hash = items[-1]["hash"] if items else "0" * 64
    entry = {
        "id": f"ev_{uuid.uuid4().hex[:6]}",
        "ts": now,
        "type": payload.type,
        "workflow": payload.workflow,
        "node": payload.node,
        "actor": payload.actor,
        "detail": payload.detail,
        "refId": payload.refId,
        "prevHash": prev_hash,
    }
    entry["hash"] = _audit_entry_hash(entry)
    items.append(entry)
    save_audit(items)
    return {"status": "success", "entry": entry}


@app.get("/audit/verify")
async def verify_audit():
    items = load_audit()
    result = _verify_audit_chain(items)
    return result


@app.get("/audit/export")
async def export_audit():
    """导出账本（PRD §6.6：满足合规审计要求）"""
    items = load_audit()
    result = _verify_audit_chain(items)
    return {
        "exportedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "verified": result["verified"],
        "total": result["total"],
        "lastHash": result["lastHash"],
        "entries": items,
    }


# ============ 外部调度开放能力（V9） ============
CAPABILITY_KINDS = ["工作流", "节点", "工具", "规则"]
CAPABILITY_STATUS_LABELS = {
    "active": "已上线",
    "pending_approval": "待审批",
    "disabled": "已下线",
}


def load_capabilities() -> Dict[str, Any]:
    if os.path.exists(CAPABILITIES_FILE):
        with open(CAPABILITIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_capabilities(data: Dict[str, Any]):
    with open(CAPABILITIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def seed_capabilities():
    """V9：预置能力暴露清单、调用日志、审批记录（PRD §6.1）"""
    store = load_capabilities()
    if store:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    store["capabilities"] = [
        {
            "id": "cap_wf_cicd", "kind": "工作流", "name": "代码变更驱动的 CI/CD 质量门禁",
            "source": "wf_cicd", "exposed": True, "status": "active",
            "protocol": "OpenAPI / 标准化工具协议", "auth": "API Key + 角色授权",
            "dangerousOps": ["运行测试", "写入缺陷"], "callCount30d": 128, "lastCalled": "2026-10-26 15:20",
            "desc": "发布时显式声明对外暴露的工作流，供外部智能体系统调度",
        },
        {
            "id": "cap_node_case_gen", "kind": "节点", "name": "代码变更驱动测试生成节点",
            "source": "wf_cicd:n_case_gen", "exposed": True, "status": "active",
            "protocol": "MCP Tool", "auth": "API Key",
            "dangerousOps": ["生成并写入用例"], "callCount30d": 56, "lastCalled": "2026-10-26 14:10",
            "desc": "单节点封装为可调用工具，支持外部系统按参数触发用例生成",
        },
        {
            "id": "cap_tool_browser", "kind": "工具", "name": "Browser-use 浏览器智能体",
            "source": "capability_pack:browser-use", "exposed": True, "status": "active",
            "protocol": "HTTP 回调", "auth": "OAuth2 客户端授权",
            "dangerousOps": ["修改资产"], "callCount30d": 342, "lastCalled": "2026-10-26 16:02",
            "desc": "认证能力包暴露为对外工具，执行类操作默认进入待审批队列",
        },
        {
            "id": "cap_rule_gate", "kind": "规则", "name": "质量门禁确定性裁决规则",
            "source": "rule:quality_gate", "exposed": False, "status": "disabled",
            "protocol": "—", "auth": "内部",
            "dangerousOps": [], "callCount30d": 0, "lastCalled": "",
            "desc": "内部规则，默认不对外暴露",
        },
        {
            "id": "cap_wf_explore", "kind": "工作流", "name": "智能探索与大规模异步回归",
            "source": "wf_explore", "exposed": True, "status": "pending_approval",
            "protocol": "OpenAPI / 标准化工具协议", "auth": "API Key + 角色授权",
            "dangerousOps": ["运行测试"], "callCount30d": 0, "lastCalled": "",
            "desc": "新发布工作流，包含执行类操作，等待平台侧审批后放行",
        },
    ]
    store["callLogs"] = [
        {"id": "call_001", "ts": "2026-10-26 15:20", "capability": "代码变更驱动的 CI/CD 质量门禁", "caller": "external-agent-7", "result": "success", "duration": "6m18s", "auditRef": "trace:run_seed_002"},
        {"id": "call_002", "ts": "2026-10-26 14:10", "capability": "代码变更驱动测试生成节点", "caller": "ci-pipeline-3", "result": "success", "duration": "42s", "auditRef": "trace:gen_088"},
        {"id": "call_003", "ts": "2026-10-26 16:02", "capability": "Browser-use 浏览器智能体", "caller": "external-agent-7", "result": "pending_approval", "duration": "—", "auditRef": "approval:cap_tool_browser"},
        {"id": "call_004", "ts": "2026-10-25 11:40", "capability": "代码变更驱动的 CI/CD 质量门禁", "caller": "ci-pipeline-1", "result": "failed", "duration": "2m01s", "auditRef": "trace:run_seed_004"},
    ]
    store["approvals"] = [
        {"id": "ap_001", "ts": "2026-10-26 16:02", "capability": "Browser-use 浏览器智能体", "op": "修改资产", "status": "待审批", "by": ""},
        {"id": "ap_002", "ts": "2026-10-26 15:20", "capability": "代码变更驱动的 CI/CD 质量门禁", "op": "运行测试", "status": "已放行", "by": "规则引擎（低风险自动放行）"},
        {"id": "ap_003", "ts": "2026-10-25 21:36", "capability": "智能探索与大规模异步回归", "op": "写入缺陷", "status": "已放行", "by": "测试负责人"},
    ]
    store["connects"] = [
        {"id": "conn_001", "caller": "external-agent-7", "keyMasked": "sk-ext-••••••••a1b2", "role": "外部智能体", "scopes": ["运行测试", "查询结果"], "status": "active", "created": "2026-09-01"},
        {"id": "conn_002", "caller": "ci-pipeline-1", "keyMasked": "sk-ci-••••••••c3d4", "role": "CI 流水线", "scopes": ["运行测试"], "status": "active", "created": "2026-08-15"},
    ]
    save_capabilities(store)


class CapabilityNew(BaseModel):
    model_config = {"extra": "allow"}
    name: str
    kind: str
    source: str = ""
    protocol: str = "OpenAPI / 标准化工具协议"
    auth: str = "API Key"
    dangerousOps: List[str] = []


class ApprovalPayload(BaseModel):
    by: str = "平台审批人"


def _with_cap_meta(c: Dict[str, Any]) -> Dict[str, Any]:
    c = dict(c)
    c["kindLabel"] = c.get("kind", "")
    c["statusLabel"] = CAPABILITY_STATUS_LABELS.get(c.get("status", ""), c.get("status", ""))
    return c


@app.get("/capabilities/meta")
async def capabilities_meta():
    return {
        "kinds": CAPABILITY_KINDS,
        "statusLabels": CAPABILITY_STATUS_LABELS,
        "note": "外部调用与内部运行共享同一审计账本；执行类操作默认进入待审批队列（PRD §6.1）。",
    }


@app.get("/capabilities")
async def list_capabilities(kind: str = "", status: str = ""):
    store = load_capabilities()
    items = store.get("capabilities", [])
    if kind:
        items = [c for c in items if c.get("kind") == kind]
    if status:
        items = [c for c in items if c.get("status") == status]
    return [_with_cap_meta(c) for c in items]


@app.post("/capabilities")
async def create_capability(payload: CapabilityNew):
    if payload.kind not in CAPABILITY_KINDS:
        raise HTTPException(status_code=400, detail="Unsupported capability kind")
    store = load_capabilities()
    caps = store.setdefault("capabilities", [])
    cid = f"cap_{uuid.uuid4().hex[:6]}"
    status = "pending_approval" if payload.dangerousOps else "active"
    cap = {
        "id": cid, "kind": payload.kind, "name": payload.name, "source": payload.source or payload.name,
        "exposed": True, "status": status, "protocol": payload.protocol, "auth": payload.auth,
        "dangerousOps": payload.dangerousOps, "callCount30d": 0, "lastCalled": "",
        "desc": "手动登记的对外能力",
    }
    caps.append(cap)
    save_capabilities(store)
    return {"status": "success", "id": cid, "capability": _with_cap_meta(cap)}


@app.get("/capabilities/call-logs")
async def capability_call_logs(capability: str = "", result: str = ""):
    store = load_capabilities()
    items = store.get("callLogs", [])
    if capability:
        items = [l for l in items if l.get("capability") == capability]
    if result:
        items = [l for l in items if l.get("result") == result]
    return items


@app.get("/capabilities/approvals")
async def capability_approvals(status: str = ""):
    store = load_capabilities()
    items = store.get("approvals", [])
    if status:
        items = [a for a in items if a.get("status") == status]
    return items


@app.post("/capabilities/approvals/{approval_id}/approve")
async def approve_capability(approval_id: str, payload: ApprovalPayload):
    store = load_capabilities()
    approvals = store.get("approvals", [])
    target = next((a for a in approvals if a.get("id") == approval_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    target["status"] = "已放行"
    target["by"] = payload.by
    target["approvedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    # 若该能力处于待审批，审批全部放行后上线
    pending = [a for a in approvals if a.get("capability") == target.get("capability") and a.get("status") == "待审批"]
    if not pending:
        for cap in store.get("capabilities", []):
            if cap.get("name") == target.get("capability") and cap.get("status") == "pending_approval":
                cap["status"] = "active"
    save_capabilities(store)
    return {"status": "success", "approval": target}


@app.get("/capabilities/connects")
async def capability_connects():
    store = load_capabilities()
    return store.get("connects", [])


def seed_audit_v9_hook():
    pass


# ============ V10 资源独占与锁（PRD §6.2）============
RESOURCE_TYPES = ["设备", "环境", "凭据", "并发槽位", "数据源"]
RESOURCE_TYPE_LABELS = {
    "设备": "📱 设备资源",
    "环境": "🧪 测试环境",
    "凭据": "🔑 凭据资源",
    "并发槽位": "🧮 并发槽位",
    "数据源": "🗄️ 数据源",
}
LOCK_MODES = ["独占锁", "共享锁"]
CONFLICT_POLICIES = ["排队等待", "直接失败", "超时释放"]
LOCK_STATUS_LABELS = {
    "locked": "锁定中",
    "free": "空闲",
    "held": "已持有",
}


def load_resources() -> Dict[str, Any]:
    if os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_resources(data: Dict[str, Any]):
    with open(RESOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def seed_resources():
    """V10：预置资源池、资源锁、锁事件、冲突队列（PRD §6.2）"""
    store = load_resources()
    if store:
        return
    store["pools"] = [
        {
            "id": "pool_device", "type": "设备", "name": "移动设备池",
            "total": 4, "locked": 3, "free": 1,
            "members": [
                {"id": "dev_a", "label": "设备 A（iPhone 15 Pro）", "status": "locked", "holder": "移动端多端回归 · n_exec_a", "ttl": 180},
                {"id": "dev_b", "label": "设备 B（Pixel 8）", "status": "locked", "holder": "移动端多端回归 · n_exec_b", "ttl": 120},
                {"id": "dev_c", "label": "设备 C（Android 模拟器）", "status": "locked", "holder": "兼容性冒烟 · n_compat", "ttl": 3600},
                {"id": "dev_d", "label": "设备 D（iPad）", "status": "free", "holder": "", "ttl": 0},
            ],
        },
        {
            "id": "pool_env", "type": "环境", "name": "测试环境池",
            "total": 2, "locked": 1, "free": 1,
            "members": [
                {"id": "env_staging", "label": "staging-web", "status": "locked", "holder": "CI/CD 门禁 · n_api_exec", "ttl": 720},
                {"id": "env_perftest", "label": "perftest-env", "status": "free", "holder": "", "ttl": 0},
            ],
        },
        {
            "id": "pool_cred", "type": "凭据", "name": "凭据资源池",
            "total": 3, "locked": 1, "free": 2,
            "members": [
                {"id": "cred_prod_ro", "label": "生产只读 DB 凭据", "status": "locked", "holder": "数据一致性节点 · n_data_check", "ttl": 300},
                {"id": "cred_sandbox", "label": "沙箱 API Key", "status": "free", "holder": "", "ttl": 0},
                {"id": "cred_ci", "label": "CI Runner Token", "status": "free", "holder": "", "ttl": 0},
            ],
        },
        {
            "id": "pool_slot", "type": "并发槽位", "name": "并行执行槽位",
            "total": 6, "locked": 4, "free": 2,
            "members": [
                {"id": "slot_1", "label": "槽位 1", "status": "locked", "holder": "并行分发 · 单元测试", "ttl": 540},
                {"id": "slot_2", "label": "槽位 2", "status": "locked", "holder": "并行分发 · 接口测试", "ttl": 480},
                {"id": "slot_3", "label": "槽位 3", "status": "locked", "holder": "并行分发 · 安全探测", "ttl": 900},
                {"id": "slot_4", "label": "槽位 4", "status": "locked", "holder": "并行分发 · 性能负载", "ttl": 600},
                {"id": "slot_5", "label": "槽位 5", "status": "free", "holder": "", "ttl": 0},
                {"id": "slot_6", "label": "槽位 6", "status": "free", "holder": "", "ttl": 0},
            ],
        },
    ]
    store["locks"] = [
        {"id": "lock_dev_a", "resourceId": "dev_a", "poolId": "pool_device", "mode": "独占锁", "holder": "移动端多端回归 · n_exec_a", "acquiredAt": "2026-10-26 15:32", "ttl": 180, "autoRelease": True, "status": "locked"},
        {"id": "lock_env_staging", "resourceId": "env_staging", "poolId": "pool_env", "mode": "独占锁", "holder": "CI/CD 门禁 · n_api_exec", "acquiredAt": "2026-10-26 16:05", "ttl": 720, "autoRelease": True, "status": "locked"},
        {"id": "lock_slot_shared", "resourceId": "slot_5", "poolId": "pool_slot", "mode": "共享锁", "holder": "探索任务 · n_browser_explore", "acquiredAt": "2026-10-26 16:40", "ttl": 300, "autoRelease": True, "status": "locked"},
        {"id": "lock_cred_prod", "resourceId": "cred_prod_ro", "poolId": "pool_cred", "mode": "独占锁", "holder": "数据一致性节点 · n_data_check", "acquiredAt": "2026-10-26 14:10", "ttl": 300, "autoRelease": False, "status": "locked"},
    ]
    store["events"] = [
        {"id": "evt_001", "ts": "2026-10-26 15:32", "resourceId": "dev_a", "action": "获取", "actor": "移动端多端回归 · n_exec_a", "detail": "获取独占锁（TTL 180s，自动释放）"},
        {"id": "evt_002", "ts": "2026-10-26 15:34", "resourceId": "dev_a", "action": "持有", "actor": "移动端多端回归 · n_exec_b", "detail": "冲突：设备 A 已占用，按排队等待策略挂起"},
        {"id": "evt_003", "ts": "2026-10-26 16:05", "resourceId": "env_staging", "action": "获取", "actor": "CI/CD 门禁 · n_api_exec", "detail": "获取独占锁（TTL 720s）"},
        {"id": "evt_004", "ts": "2026-10-26 16:41", "resourceId": "slot_5", "action": "获取", "actor": "探索任务 · n_browser_explore", "detail": "获取共享锁，允许并发读取"},
        {"id": "evt_005", "ts": "2026-10-26 14:12", "resourceId": "cred_prod_ro", "action": "释放", "actor": "数据一致性节点 · n_data_check", "detail": "节点完成，主动释放独占锁"},
    ]
    store["queue"] = [
        {"id": "q_001", "ts": "2026-10-26 15:34", "resourceId": "dev_a", "requester": "移动端多端回归 · n_exec_b", "policy": "排队等待", "waitSec": 180},
    ]
    save_resources(store)


class PoolNew(BaseModel):
    model_config = {"extra": "allow"}
    type: str
    name: str
    members: List[Dict[str, Any]] = []


class LockAcquire(BaseModel):
    model_config = {"extra": "allow"}
    resourceId: str
    holder: str
    mode: str = "独占锁"
    ttl: int = 600
    policy: str = "排队等待"


class LockRelease(BaseModel):
    model_config = {"extra": "allow"}
    by: str = ""


def _with_resource_meta(item: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(item)
    item["typeLabel"] = RESOURCE_TYPE_LABELS.get(item.get("type", ""), item.get("type", ""))
    return item


@app.get("/resources/meta")
async def resources_meta():
    return {
        "types": RESOURCE_TYPES,
        "typeLabels": RESOURCE_TYPE_LABELS,
        "lockModes": LOCK_MODES,
        "policies": CONFLICT_POLICIES,
        "note": "资源锁具备超时自动回收；锁冲突不导致死锁；锁事件可追溯（PRD §6.2）。",
    }


@app.get("/resources/pools")
async def list_resource_pools(type: str = ""):
    store = load_resources()
    pools = store.get("pools", [])
    if type:
        pools = [p for p in pools if p.get("type") == type]
    return [_with_resource_meta(p) for p in pools]


@app.post("/resources/pools")
async def create_resource_pool(payload: PoolNew):
    if payload.type not in RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported resource type")
    store = load_resources()
    pools = store.setdefault("pools", [])
    pid = f"pool_{uuid.uuid4().hex[:6]}"
    members = payload.members or []
    pool = {
        "id": pid, "type": payload.type, "name": payload.name,
        "total": len(members), "locked": 0, "free": len(members),
        "members": members,
    }
    pools.append(pool)
    save_resources(store)
    return {"status": "success", "id": pid, "pool": _with_resource_meta(pool)}


@app.get("/resources/locks")
async def list_resource_locks(poolId: str = "", status: str = ""):
    store = load_resources()
    locks = store.get("locks", [])
    if poolId:
        locks = [l for l in locks if l.get("poolId") == poolId]
    if status:
        locks = [l for l in locks if l.get("status") == status]
    return locks


@app.post("/resources/locks")
async def acquire_resource_lock(payload: LockAcquire):
    store = load_resources()
    locks = store.setdefault("locks", [])
    # 检查资源是否已被独占持有
    target = next((l for l in locks if l.get("resourceId") == payload.resourceId and l.get("status") == "locked"), None)
    lock = {
        "id": f"lock_{uuid.uuid4().hex[:6]}", "resourceId": payload.resourceId, "poolId": "",
        "mode": payload.mode, "holder": payload.holder,
        "acquiredAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ttl": payload.ttl, "autoRelease": True, "status": "locked",
    }
    locks.append(lock)
    events = store.setdefault("events", [])
    if target and target["mode"] == "独占锁" and payload.mode == "独占锁":
        queue = store.setdefault("queue", [])
        queue.append({
            "id": f"q_{uuid.uuid4().hex[:6]}", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resourceId": payload.resourceId, "requester": payload.holder,
            "policy": payload.policy, "waitSec": payload.ttl,
        })
        events.append({"id": f"evt_{uuid.uuid4().hex[:6]}", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "resourceId": payload.resourceId, "action": "持有", "actor": payload.holder,
                       "detail": f"冲突：资源已占用，按 {payload.policy} 策略处理"})
    else:
        events.append({"id": f"evt_{uuid.uuid4().hex[:6]}", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "resourceId": payload.resourceId, "action": "获取", "actor": payload.holder,
                       "detail": f"获取 {payload.mode}（TTL {payload.ttl}s）"})
    save_resources(store)
    return {"status": "success", "lock": lock}


@app.post("/resources/locks/{lock_id}/release")
async def release_resource_lock(lock_id: str, payload: LockRelease):
    store = load_resources()
    locks = store.get("locks", [])
    target = next((l for l in locks if l.get("id") == lock_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Lock not found")
    target["status"] = "free"
    target["releasedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target["releasedBy"] = payload.by or target.get("holder", "")
    events = store.setdefault("events", [])
    events.append({"id": f"evt_{uuid.uuid4().hex[:6]}", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "resourceId": target.get("resourceId"), "action": "释放",
                   "actor": payload.by or target.get("holder", ""),
                   "detail": "主动释放锁"})
    save_resources(store)
    return {"status": "success", "lock": target}


@app.get("/resources/events")
async def resource_events(resourceId: str = "", action: str = ""):
    store = load_resources()
    events = store.get("events", [])
    if resourceId:
        events = [e for e in events if e.get("resourceId") == resourceId]
    if action:
        events = [e for e in events if e.get("action") == action]
    return events


@app.get("/resources/queue")
async def resource_conflict_queue(policy: str = ""):
    store = load_resources()
    queue = store.get("queue", [])
    if policy:
        queue = [q for q in queue if q.get("policy") == policy]
    return queue


@app.get("/resources/summary")
async def resource_summary():
    store = load_resources()
    pools = store.get("pools", [])
    locks = store.get("locks", [])
    active = [l for l in locks if l.get("status") == "locked"]
    return {
        "poolCount": len(pools),
        "totalMembers": sum(p.get("total", 0) for p in pools),
        "lockedCount": sum(1 for p in pools for m in p.get("members", []) if m.get("status") == "locked"),
        "activeLocks": len(active),
        "queueCount": len(store.get("queue", [])),
        "eventCount": len(store.get("events", [])),
    }


# ============ V11 统一配置中心（PRD §6.8 / §6.9）============
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
SETTINGS_SECTIONS = ["驱动", "模型", "通知", "环境检测", "权限控制"]
POLICY_OVERRIDES = ["硬停止", "降级输出", "升级人工"]


def load_settings() -> Dict[str, Any]:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(data: Dict[str, Any]):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def seed_settings():
    """V11：预置 5 分区统一配置 + 预算策略（PRD §6.8 / §6.9）"""
    store = load_settings()
    if store:
        return
    store["sections"] = {
        "驱动": {
            "id": "sec_driver", "label": "驱动配置", "enabled": True,
            "items": [
                {"key": "浏览器驱动", "value": "Playwright Chromium", "type": "select", "options": ["Playwright Chromium", "Selenium Chrome", "Airtest"], "desc": "UI 探索 / Browser-use 节点使用的浏览器驱动"},
                {"key": "移动端驱动", "value": "Airtest 1.3.0", "type": "select", "options": ["Airtest 1.3.0", "Appium 2.x"], "desc": "移动端图像识别自动化节点驱动"},
                {"key": "设备连接协议", "value": "USB + ADB", "type": "select", "options": ["USB + ADB", "无线 ADB", "远程设备云"], "desc": "设备池连接方式"},
            ],
        },
        "模型": {
            "id": "sec_model", "label": "模型配置", "enabled": True,
            "items": [
                {"key": "默认文本模型", "value": "Claude-Sonnet-4.5", "type": "select", "options": ["Claude-Sonnet-4.5", "Qwen3-Max", "GPT-4o", "Gemini-2.5-Pro"], "desc": "规划 / 执行 / 验证节点默认文本模型"},
                {"key": "默认视觉模型", "value": "Claude-Opus-4.5-Vision", "type": "select", "options": ["Claude-Opus-4.5-Vision", "Gemini-2.5-Pro", "GPT-4o"], "desc": "视觉 / 语义回归节点默认视觉模型"},
                {"key": "推理温度", "value": "0.2", "type": "number", "options": [], "desc": "测试场景低温度保证可重复"},
                {"key": "Top-P", "value": "0.9", "type": "number", "options": [], "desc": "核采样阈值"},
            ],
        },
        "通知": {
            "id": "sec_notify", "label": "通知配置", "enabled": True,
            "items": [
                {"key": "通知渠道", "value": "钉钉 + 邮件", "type": "multi", "options": ["钉钉", "飞书", "邮件", "Slack", "Webhook"], "desc": "门禁裁决 / 缺陷归档触发的通知渠道"},
                {"key": "门禁阻断通知", "value": "on", "type": "switch", "options": ["on", "off"], "desc": "质量门禁阻断时立即推送"},
                {"key": "超时升级通知", "value": "on", "type": "switch", "options": ["on", "off"], "desc": "任务超时 / 无进展熔断时升级人工并通知"},
                {"key": "静默时段", "value": "23:00-07:00", "type": "text", "options": [], "desc": "非紧急通知在静默时段不推送"},
            ],
        },
        "环境检测": {
            "id": "sec_env", "label": "环境检测", "enabled": True,
            "items": [
                {"key": "环境探针", "value": "每 60s 一次", "type": "select", "options": ["每 30s 一次", "每 60s 一次", "仅执行前检测"], "desc": "执行节点前对目标环境做可达性 / 版本探针"},
                {"key": "数据源连接池", "value": "maxsize=10, timeout=30s", "type": "text", "options": [], "desc": "数据库 / 数据一致性节点连接池参数"},
                {"key": "破坏性测试熔断", "value": "enabled", "type": "switch", "options": ["enabled", "disabled"], "desc": "安全探测节点越界操作自动熔断（平台级红线，不可被节点覆盖）"},
            ],
        },
        "权限控制": {
            "id": "sec_perm", "label": "权限控制", "enabled": True,
            "items": [
                {"key": "角色模型", "value": "RBAC", "type": "select", "options": ["RBAC", "ABAC"], "desc": "开放能力接入的角色授权模型"},
                {"key": "危险操作审批方", "value": "测试负责人", "type": "select", "options": ["测试负责人", "平台审批人", "规则引擎自动放行"], "desc": "执行类 / 写入类操作默认审批方"},
                {"key": "审计账本只读角色", "value": "合规审计员", "type": "text", "options": [], "desc": "可导出但不可修改审计账本的角色"},
                {"key": "密钥明文落盘", "value": "forbidden", "type": "switch", "options": ["forbidden", "allowed"], "desc": "凭据与模型密钥禁止明文落盘（平台红线）"},
            ],
        },
    }
    store["budgets"] = [
        {"id": "budget_node", "scope": "节点级", "tokenBudget": 50000, "timeBudgetSec": 600, "onExceed": "硬停止", "desc": "单节点默认预算，超出即终止"},
        {"id": "budget_wf", "scope": "工作流级", "tokenBudget": 500000, "timeBudgetSec": 3600, "onExceed": "降级输出", "desc": "单工作流总预算，超出降级为部分结果"},
        {"id": "budget_loop", "scope": "循环节点", "maxIterations": 8, "noProgressFuse": 3, "onExceed": "升级人工", "desc": "循环节点最大迭代与无进展熔断次数"},
    ]
    save_settings(store)


class SectionItemUpdate(BaseModel):
    key: str
    value: str = ""


class BudgetUpdate(BaseModel):
    model_config = {"extra": "allow"}
    scope: str = ""
    tokenBudget: Optional[int] = None
    timeBudgetSec: Optional[int] = None
    onExceed: str = ""


@app.get("/settings/meta")
async def settings_meta():
    return {
        "sections": SETTINGS_SECTIONS,
        "policies": POLICY_OVERRIDES,
        "note": "统一配置中心集中管理驱动、模型、通知、环境检测与权限控制，预算强制由平台代码执行（PRD §6.8 / §6.9）。",
    }


@app.get("/settings")
async def list_settings_sections():
    store = load_settings()
    sections = store.get("sections", {})
    return [dict(s, key=k) for k, s in sections.items()]


@app.put("/settings/sections/{section_key}/items/{item_key}")
async def update_setting_item(section_key: str, item_key: str, payload: SectionItemUpdate):
    store = load_settings()
    sections = store.get("sections", {})
    # GET /settings 在返回值上附加 key（dict 键，如 "驱动"）；PUT 请求携带的就是该 key，
    # 因此查找需同时兼容 dict 键 / label / id 三种形式
    sec = next((s for k, s in sections.items() if k == section_key or s.get("label") == section_key or s.get("id") == section_key), None)
    if sec is None:
        raise HTTPException(status_code=404, detail="Section not found")
    item = next((i for i in sec.get("items", []) if i.get("key") == item_key), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    item["value"] = payload.value
    item["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_settings(store)
    return {"status": "success", "section": section_key, "item": item}


@app.get("/settings/budgets")
async def list_setting_budgets():
    store = load_settings()
    return store.get("budgets", [])


@app.put("/settings/budgets/{budget_id}")
async def update_setting_budget(budget_id: str, payload: BudgetUpdate):
    store = load_settings()
    budgets = store.get("budgets", [])
    target = next((b for b in budgets if b.get("id") == budget_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    if payload.tokenBudget is not None:
        target["tokenBudget"] = payload.tokenBudget
    if payload.timeBudgetSec is not None:
        target["timeBudgetSec"] = payload.timeBudgetSec
    if payload.onExceed:
        if payload.onExceed not in POLICY_OVERRIDES:
            raise HTTPException(status_code=400, detail="Unsupported policy")
        target["onExceed"] = payload.onExceed
    target["updatedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_settings(store)
    return {"status": "success", "budget": target}


async def run_execution_engine(exec_id: str, workflow: Dict[str, Any]):
    nodes = workflow["nodes"]
    edges = workflow["edges"]
    state = execution_registry[exec_id]

    start_node = next((n for n in nodes if "开始" in n["label"]), nodes[0]) if nodes else None
    if start_node is None:
        state["status"] = "failed"
        state["logs"].append({"nodeId": "global", "msg": "工作流没有节点，无法执行", "time": "now"})
        return

    node_map = {n["id"]: n for n in nodes}
    total_tokens = 0
    total_cost = 0.0
    seq = 0

    current_node_id = start_node["id"]
    visited = set()

    while current_node_id and current_node_id not in visited:
        visited.add(current_node_id)
        seq += 1
        node_obj = node_map.get(current_node_id)
        node_label = node_obj["label"] if node_obj else current_node_id
        cfg = (node_obj or {}).get("config", {}) if node_obj else {}

        # 模拟 Token / 成本
        tokens = 800 + (len(cfg.get("systemPrompt", "")) + len(cfg.get("userPrompt", ""))) // 4
        cost = round(tokens * 0.000005, 4)
        total_tokens += tokens
        total_cost += cost

        state["node_states"][current_node_id] = "running"
        state["logs"].append({
            "nodeId": current_node_id, "msg": f"节点「{node_label}」开始执行（模型 {cfg.get('model', 'Claude-Opus-4.5')}）", "time": "now",
        })

        await asyncio.sleep(1.0)

        # 模拟工具调用（白名单）
        tools = cfg.get("toolWhitelist", []) or []
        if tools:
            state["logs"].append({
                "nodeId": current_node_id,
                "msg": f"工具调用: {', '.join(tools[:3])}",
                "time": "now",
            })

        # 关键判定：质量门禁 / 充分性评估 的归因叙述（模型生成）+ 确定性裁决（规则引擎）
        verdict = None
        if node_label in ("质量门禁", "测试充分性评估", "计划确认门", "人工审批门"):
            verdict = "通过"
            state["logs"].append({
                "nodeId": current_node_id,
                "msg": f"门禁裁决（规则引擎）: {verdict} · 归因叙述（模型）: 主要贡献因素为执行通过率与覆盖率",
                "time": "now",
            })

        state["node_states"][current_node_id] = "success"
        state["logs"].append({
            "nodeId": current_node_id,
            "msg": f"节点「{node_label}」执行成功 · Token {tokens} · 成本 ¥{cost:.4f}",
            "time": "now",
        })

        state["timeline"].append({
            "seq": seq,
            "nodeId": current_node_id,
            "label": node_label,
            "status": "success",
            "started": now_str(),
            "duration": "1.0s",
            "tokens": tokens,
            "cost": cost,
            "model": cfg.get("model", "Claude-Opus-4.5"),
            "input": {
                "binding": f"$.{current_node_id}.input" if seq > 1 else "trigger.payload",
                "payload": cfg.get("inputBindings") or {"workflow": workflow.get("id", workflow.get("name"))},
            },
            "reasoning": f"{node_label} 节点按配置完成模拟推理，输出结构化结果。",
            "tools": tools,
            "output": {
                "status": "success",
                "tokens": tokens,
                "cost": cost,
            },
            "evidence": [f"trace:{current_node_id}:{seq}", f"log:{current_node_id}:{seq}"],
            "gate": ({"verdict": verdict, "engine": "确定性规则引擎", "narrative": "主要贡献因素为执行通过率与覆盖率"} if verdict else None),
        })

        next_edge = next((e for e in edges if e["source"] == current_node_id), None)
        current_node_id = next_edge["target"] if next_edge else None

    state["status"] = "completed"
    state["tokens"] = total_tokens
    state["cost"] = round(total_cost, 4)
    state["duration"] = f"{seq * 1.0:.1f}s"
    state["gate"] = next((t.get("gate") for t in reversed(state["timeline"]) if t.get("gate")), None)
    state["logs"].append({
        "nodeId": "global",
        "msg": f"工作流执行完毕 · 总 Token {total_tokens} · 总成本 ¥{total_cost:.4f}",
        "time": "now",
    })

    # V4：把完成的运行记录持久化到 runs.json
    run = {
        "id": exec_id,
        "workflow_id": workflow.get("id", workflow.get("workflow_id", "")),
        "workflow_name": state.get("workflow_name", workflow.get("name", "")),
        "trigger": "手动",
        "status": "completed",
        "started": state.get("started", now_str()),
        "duration": state["duration"],
        "tokens": total_tokens,
        "cost": round(total_cost, 4),
        "gate": state["gate"],
        "node_states": state["node_states"],
        "timeline": state["timeline"],
        "logs": state["logs"],
        "created": now_str(),
    }
    runs = load_runs()
    runs[exec_id] = run
    save_runs(runs)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
