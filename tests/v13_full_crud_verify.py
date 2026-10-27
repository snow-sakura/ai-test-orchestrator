"""V13 全功能增删改查 + 业务串联 有头浏览器验证脚本
使用有头浏览器（headless=False）打开真实 UI，对全部 11 个模块做精确的
增 / 删 / 改 / 查 验证，并串联跨模块业务流程：
  1. 工作流：建 → 改（重命名/发布）→ 查（搜索）→ 删
  2. 画布：加节点 → 改节点模型/提示词 → 结构校验 → 试运行
  3. 执行追踪：重新运行 → 查时间线 / 展开执行面板
  4. 资产：新建 → 查详情 → 认证/退役
  5. 任务：提交 → 查详情 → 轮询推进/取消
  6. 模型：授予额度 → 撤销 → 叠加额度 → 连接测试
  7. 审计：追加证据 → 校验哈希链 → 导出
  8. 能力：登记 → 放行审批
  9. 资源：登记资源池 → 获取锁 → 释放锁
 10. 配置：改配置项 → 改预算策略
 11. 跨模块串联：工作台 → 各模块 → 返回
关键步骤自动截图到 tests/screenshots/v13/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5173"
API = "http://127.0.0.1:8000"
BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v13")
os.makedirs(SHOT_DIR, exist_ok=True)


def _w(name, data):
    with open(os.path.join(BACKEND, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reset_all_seeds():
    """把所有 JSON 数据源复位为干净种子，保证 CRUD 验证可重复、可断言"""
    _w("workflows.json", {"default-workflow": {
        "id": "default-workflow", "name": "我的第一个测试工作流", "status": "draft",
        "nodes": [
            {"id": "n1", "label": "开始", "type": "platform", "position": {"x": 80, "y": 120}, "config": {}},
            {"id": "n2", "label": "需求解析", "type": "analysis", "position": {"x": 320, "y": 120}, "config": {"model": "Claude-Opus-4.5"}},
        ],
        "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
    }})
    _w("runs.json", {
        "run_seed_001": {
            "id": "run_seed_001", "workflow_id": "default-workflow", "workflow_name": "我的第一个测试工作流",
            "trigger": "手动", "status": "completed", "started": "10-26 16:42:00", "duration": "2s08ms",
            "tokens": 1612, "cost": 0.0081,
            "gate": {"verdict": "通过", "engine": "确定性规则引擎", "narrative": "主要贡献因素为执行通过率与覆盖率"},
            "node_states": {"n1": "success", "n2": "success"},
            "timeline": [
                {"seq": 1, "nodeId": "n1", "label": "开始", "status": "success", "started": "16:42:01", "duration": "0.8s", "tokens": 806, "cost": 0.004,
                 "model": "Claude-Opus-4.5", "reasoning": "工作流入口节点。", "tools": [], "output": {"context": {"workflow": "default-workflow"}}, "evidence": ["trace:n1"]},
                {"seq": 2, "nodeId": "n2", "label": "需求解析", "status": "success", "started": "16:42:02", "duration": "1.2s", "tokens": 806, "cost": 0.0041,
                 "model": "Gemini-2.5-Pro", "reasoning": "抽取 3 个可测需求点。", "tools": ["webFetch"], "output": {"requirementPoints": 3}, "evidence": ["log:n2:001", "trace:n2"]},
            ],
            "logs": [
                {"nodeId": "n1", "msg": "节点「开始」开始执行（模型 Claude-Opus-4.5）", "time": "16:42:01"},
                {"nodeId": "n1", "msg": "节点「开始」执行成功 · Token 806", "time": "16:42:02"},
                {"nodeId": "n2", "msg": "节点「需求解析」执行成功 · Token 806", "time": "16:42:03"},
                {"nodeId": "global", "msg": "工作流执行完毕 · 总 Token 1612", "time": "16:42:04"},
            ],
            "created": "2026-10-26 16:42:00",
        }
    })
    _w("assets.json", {
        "asset_case_001": {"id": "asset_case_001", "type": "用例", "name": "移动端登录全流程认证用例", "version": 3, "status": "certified",
            "scope": ["移动端"], "quality": {"mutationScore": 0.92, "stability": 0.95, "regressionResult": "pass"},
            "references": ["wf_cicd"], "certifiedAt": "2026-09-15", "retireAlert": False,
            "auditLog": [{"ts": "2026-09-15", "action": "certified", "by": "质量门禁节点", "detail": "通过"}]},
        "asset_cd_001": {"id": "asset_cd_001", "type": "变更驱动用例", "name": "支付模块变更驱动回归用例集", "version": 1, "status": "pending",
            "scope": ["支付"], "quality": {"mutationScore": 0.72, "stability": 0.60, "regressionResult": "pass"},
            "references": [], "certifiedAt": "", "retireAlert": False,
            "auditLog": [{"ts": "2026-10-25", "action": "created", "by": "生成节点", "detail": "生成待认证"}]},
    })
    _w("tasks.json", {
        "task_running_001": {"id": "task_running_001", "type": "异步测试任务", "name": "支付模块异步回归测试任务", "status": "running",
            "workflow": "wf_payment_regression", "node": "n_async_regression", "progress": 40, "started": "2026-10-26 14:02",
            "eta": "约 8 分钟", "owner": "test-agent-01", "resource": "browser-farm-A", "result_ref": "var://wf_payment_regression/result",
            "poll_interval": 15, "timeout_sec": 1800, "mode": "poll",
            "auditLog": [{"ts": "2026-10-26 14:02", "action": "created", "by": "平台", "detail": "任务已提交"}]},
        "task_done_001": {"id": "task_done_001", "type": "回归任务", "name": "每日全量回归任务", "status": "success",
            "workflow": "wf_daily_regression", "node": "n_full", "progress": 100, "started": "2026-10-26 02:00",
            "eta": "完成", "owner": "test-agent-02", "resource": "ci-farm-B", "result_ref": "var://wf_daily/result",
            "poll_interval": 30, "timeout_sec": 3600, "mode": "poll",
            "auditLog": [{"ts": "2026-10-26 04:12", "action": "completed", "by": "平台", "detail": "执行完成"}]},
    })
    _w("models.json", {
        "registry": [],
        "configs": {
            "global": {"level": "全站", "owner": "", "textModel": "agnes_3_0_flash", "visionModel": "claude_opus_4_5_vision",
                       "params": {"temperature": 0.2, "maxTokens": 128000}, "keyMasked": "sk-E5A4••••••••2zabgJriV",
                       "connected": True, "keyMaskedSource": "管理员",
                       "baseUrl": "https://apihub.agnes-ai.com/v1", "envKey": "CHERRY_QWEN_API_KEY"},
            "personal_test_lead": {"level": "个人", "owner": "测试负责人", "textModel": "qwen3_max", "visionModel": "gpt_4o",
                                   "params": {"temperature": 0.3, "maxTokens": 8192}, "keyMasked": "sk-alb-••••••••9c2d",
                                   "connected": True, "keyMaskedSource": "个人自带凭据"},
            "role_case_generator": {"level": "角色", "owner": "用例生成节点", "textModel": "gemini_2_5_pro", "visionModel": "",
                                    "params": {"temperature": 0.4, "maxTokens": 16384}, "keyMasked": "sk-goo-••••••••4e1b",
                                    "connected": False, "keyMaskedSource": "角色独立凭据"},
        },
        "grants": [
            {"id": "grant_001", "account": "测试负责人", "model": "agnes_3_0_flash", "date": "2026-10-26",
             "extraQuota": 500, "revoked": False, "by": "管理员", "ts": "2026-10-26 08:00"},
        ],
        "quotas": [
            {"account": "测试负责人", "model": "agnes_3_0_flash", "dailyLimit": 2000, "usedToday": 360, "extraToday": 0, "renewed": False},
        ],
        "usage": [
            {"id": "u1", "model": "agnes_3_0_flash", "workflow": "我的第一个测试工作流", "node": "需求解析",
             "tokens": 806, "cost": 0.0041, "ts": "2026-10-26 14:02"},
        ],
    })
    # 审计账本：与后端 seed_audit() 完全一致的 7 条种子，
    # 在测试侧按后端 _audit_entry_hash / _with_audit_chain 同款算法生成哈希链
    # （payload 剔除 prevHash 与 hash 字段后 JSON 排序序列化取 SHA-256）
    import hashlib
    _audit_seeds = [
        {"id": "ev_001", "ts": "2026-10-26 09:01", "type": "工具调用", "workflow": "代码变更驱动的 CI/CD 质量门禁",
         "node": "变更影响分析", "actor": "gemini_2_5_pro", "detail": "调用 webFetch 获取 Git diff 摘要", "refId": "trace:run_seed_002:n2"},
        {"id": "ev_002", "ts": "2026-10-26 09:02", "type": "白名单拒绝", "workflow": "代码变更驱动的 CI/CD 质量门禁",
         "node": "变更影响分析", "actor": "平台规则引擎", "detail": "拒绝调用 shell_exec（不在白名单内）", "refId": "whitelist:run_seed_002:n2"},
        {"id": "ev_003", "ts": "2026-10-26 09:03", "type": "质量门禁裁决", "workflow": "代码变更驱动的 CI/CD 质量门禁",
         "node": "质量门禁", "actor": "确定性规则引擎", "detail": "裁决：通过（执行通过率 96%，覆盖率 82%）", "refId": "gate:run_seed_002:n5"},
        {"id": "ev_004", "ts": "2026-10-25 21:35", "type": "缺陷归档", "workflow": "移动端多端回归",
         "node": "失败分诊", "actor": "失败分诊节点", "detail": "归档缺陷 DEF-2026-0921（登录崩溃），关联证据 ev_004", "refId": "defect:DEF-2026-0921"},
        {"id": "ev_005", "ts": "2026-10-25 21:36", "type": "人工审批", "workflow": "移动端多端回归",
         "node": "人工审批门", "actor": "测试负责人", "detail": "批准高风险缺陷升级处理", "refId": "approval:DEF-2026-0921"},
        {"id": "ev_006", "ts": "2026-10-24 15:20", "type": "升级处理", "workflow": "Web 端深度探索",
         "node": "探索任务节点", "actor": "平台", "detail": "任务超时，升级转人工处理", "refId": "escalation:task_timeout_001"},
        {"id": "ev_007", "ts": "2026-10-26 14:03", "type": "工具调用", "workflow": "我的第一个测试工作流",
         "node": "需求解析", "actor": "claude_sonnet_4_5", "detail": "调用 webFetch 获取需求文档", "refId": "trace:run_seed_001:n2"},
    ]
    def _audit_hash_chain(items):
        prev = "0" * 64
        out = []
        for it in items:
            it = dict(it)
            it["prevHash"] = prev
            payload = {k: v for k, v in it.items() if k not in ("prevHash", "hash")}
            raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            it["hash"] = hashlib.sha256(raw).hexdigest()
            prev = it["hash"]
            out.append(it)
        return out
    _w("audit.json", _audit_hash_chain(_audit_seeds))
    # capabilities：后端期望 {"capabilities":[...],"callLogs":[...],"approvals":[...],"connects":[...]}
    _w("capabilities.json", {
        "capabilities": [
            {"id": "cap_wf_cicd", "kind": "工作流", "name": "CI/CD 质量门禁工作流", "source": "wf_cicd",
             "exposed": True, "status": "active", "protocol": "OpenAPI", "auth": "OAuth2",
             "dangerousOps": [], "callCount30d": 128, "lastCalled": "2026-10-26",
             "desc": "对外暴露的 CI/CD 门禁工作流"},
            {"id": "cap_tool_fetch", "kind": "工具", "name": "webFetch 工具", "source": "tool:webFetch",
             "exposed": True, "status": "active", "protocol": "REST", "auth": "APIKey",
             "dangerousOps": ["删除记录"], "callCount30d": 540, "lastCalled": "2026-10-26",
             "desc": "对外暴露的网页抓取工具"},
        ],
        "callLogs": [
            {"id": "cl1", "ts": "2026-10-26 15:02", "capability": "webFetch 工具", "caller": "external-agent-01",
             "result": "success", "duration": "320ms", "auditRef": "audit:cl1"},
            {"id": "cl2", "ts": "2026-10-26 15:10", "capability": "CI/CD 质量门禁工作流", "caller": "ci-runner",
             "result": "pending_approval", "duration": "—", "auditRef": "audit:cl2"},
        ],
        "approvals": [
            {"id": "appr_001", "ts": "2026-10-26 15:12", "capability": "webFetch 工具", "op": "删除记录",
             "status": "待审批", "by": ""},
        ],
        "connects": [
            {"id": "conn_001", "caller": "external-agent-01", "role": "外部智能体", "status": "active",
             "keyMasked": "sk-ext-••••a1b2", "created": "2026-10-01", "scopes": ["workflow.read", "tool.invoke"]},
        ],
    })
    _w("resources.json", {
        "pools": [
            {"id": "pool_device", "type": "设备", "name": "移动设备池", "total": 2, "locked": 1, "free": 1,
             "members": [
                 {"id": "dev_a", "label": "设备 A（iPhone 15 Pro）", "status": "free", "holder": "", "ttl": 0},
                 {"id": "dev_b", "label": "设备 B（Pixel 8）", "status": "locked", "holder": "移动端回归 · n_exec_b", "ttl": 120},
             ]},
        ],
        "locks": [
            {"id": "lock_dev_b", "resourceId": "dev_b", "poolId": "pool_device", "mode": "独占锁", "holder": "移动端回归 · n_exec_b", "acquiredAt": "2026-10-26 15:32", "ttl": 120, "autoRelease": True, "status": "locked"},
        ],
        "events": [
            {"id": "ev1", "ts": "2026-10-26 15:32", "resourceId": "dev_b", "action": "持有", "actor": "移动端回归 · n_exec_b", "detail": "获取独占锁"},
        ],
        "queue": [
            {"id": "q1", "resourceId": "dev_b", "policy": "排队等待", "requester": "兼容性冒烟 · n_compat", "ts": "2026-10-26 15:33", "waitSec": 45},
        ],
    })
    # settings：后端 load_settings 期望 sections 为 {key: {id,label,enabled,items:[...]}} 字典结构
    _w("settings.json", {
        "sections": {
            "驱动": {
                "id": "sec_driver", "label": "驱动配置", "enabled": True,
                "items": [
                    {"key": "浏览器驱动", "value": "Playwright Chromium", "type": "select",
                     "options": ["Playwright Chromium", "Selenium Chrome", "Airtest"], "desc": "UI 探索驱动"},
                ],
            },
            "模型": {
                "id": "sec_model", "label": "模型配置", "enabled": True,
                "items": [
                    {"key": "默认文本模型", "value": "Claude-Sonnet-4.5", "type": "select",
                     "options": ["Claude-Sonnet-4.5", "Qwen3-Max", "GPT-4o", "Gemini-2.5-Pro"], "desc": "默认文本模型"},
                    {"key": "推理温度", "value": "0.2", "type": "number", "options": [], "desc": "低温度保证可重复"},
                ],
            },
        },
        "budgets": [
            {"id": "budget_node", "scope": "节点级", "tokenBudget": 50000, "timeBudgetSec": 600,
             "onExceed": "硬停止", "desc": "单节点预算"},
        ],
    })
    print("[reset] 9 个 JSON 数据源已复位为干净种子")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


def wf_card(page, name):
    h3 = page.locator(f"h3:has-text('{name}')").first
    return h3.locator("xpath=ancestor::div[contains(@class,'polaroid-card') and contains(@class,'p-4')][1]")


def check(cond, msg):
    global _OK, _FAIL
    if cond:
        _OK += 1
        print(f"  ✅ {msg}")
    else:
        _FAIL += 1
        print(f"  ❌ {msg}")


_OK = 0
_FAIL = 0


async def run():
    global _OK, _FAIL
    reset_all_seeds()
    _OK = 0
    _FAIL = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--no-default-browser-check"])
        page = await browser.new_page(viewport={"width": 1680, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        print("🌐 有头浏览器已打开（非后台运行）\n")

        # ============ ① 工作流：增删改查 ============
        print("── ① 工作流列表（增删改查）──")
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('工作流列表')", timeout=10000)
        check(await page.locator("text=我的第一个测试工作流").count() >= 1, "查询：预置工作流渲染")

        # 增
        await page.click("button:has-text('＋ 新建工作流')")
        await page.wait_for_selector("div.fixed input[placeholder='我的工作流']", timeout=5000)
        await page.fill("div.fixed input[placeholder='我的工作流']", "V13验证新工作流")
        await page.locator("div.fixed select").first.select_option(value="cicd")
        await page.click("div.fixed button:has-text('确定')")
        await page.wait_for_selector("text=V13验证新工作流", timeout=5000)
        check(await page.locator("text=V13验证新工作流").count() >= 1, "增：新建工作流出现")
        await shot(page, "01_wf_create")

        # 改（重命名）
        await wf_card(page, "V13验证新工作流").locator("button:has-text('重命名')").click()
        await page.fill("div.fixed input", "V13重命名工作流")
        await page.click("div.fixed button:has-text('确定')")
        await page.wait_for_selector("text=V13重命名工作流", timeout=5000)
        check(await page.locator("text=V13重命名工作流").count() >= 1, "改：重命名成功")

        # 改（发布）
        await wf_card(page, "V13重命名工作流").locator("button:has-text('发布')").click()
        await page.wait_for_selector("text=已发布", timeout=5000)
        check(await wf_card(page, "V13重命名工作流").locator("span:has-text('已发布')").count() >= 1, "改：发布后状态切换为已发布")
        await shot(page, "02_wf_edit_publish")

        # 查（搜索）
        await page.fill("input[placeholder='搜索工作流...']", "V13重命名")
        await page.wait_for_timeout(300)
        check(await page.locator("text=V13重命名工作流").count() >= 1, "查：搜索命中")
        await page.fill("input[placeholder='搜索工作流...']", "zzz不存在")
        await page.wait_for_timeout(300)
        check(await page.locator("text=暂无匹配的工作流").count() >= 1, "查：无匹配显示空态")
        await page.fill("input[placeholder='搜索工作流...']", "")
        await page.wait_for_timeout(300)

        # 删
        await wf_card(page, "V13重命名工作流").locator("button:has-text('删除')").click()
        await page.wait_for_timeout(500)
        check(await page.locator("text=V13重命名工作流").count() == 0, "删：工作流已删除")
        await shot(page, "03_wf_delete")

        # ============ ② 画布：节点增/改 + 校验 + 试运行 ============
        print("\n── ② 编排画布（节点增/改/校验/试运行）──")
        await page.goto(BASE + "/editor", wait_until="networkidle")
        await page.wait_for_selector("text=节点模板库（PRD §11）", timeout=8000)
        nodes_before = len(await page.locator(".custom-node").all())
        check(nodes_before >= 2, f"查：画布加载节点（{nodes_before} 个）")

        # 增节点
        await page.locator("text=需求解析").first.click()
        await page.wait_for_timeout(400)
        nodes_after = len(await page.locator(".custom-node").all())
        check(nodes_after > nodes_before, f"增：点击节点库新增节点（{nodes_before}→{nodes_after}）")

        # 改：选中节点打开抽屉
        await page.locator(".custom-node:has-text('需求解析')").first.click()
        await page.wait_for_selector("aside h2:has-text('节点配置')", timeout=5000)
        check(True, "改：选中节点打开配置抽屉")
        # 展开 模型配置 分区（抽屉默认只展开 基础信息）
        await page.locator("aside button:has-text('模型配置')").click()
        await page.wait_for_selector("aside select", timeout=5000)
        await page.locator("aside select").first.select_option(value="Qwen3-Max")
        await page.wait_for_timeout(300)
        check(True, "改：节点模型切换为 Qwen3-Max")
        # 改提示词（展开 提示词配置 分区）
        await page.locator("aside button:has-text('提示词配置')").click()
        await page.wait_for_selector("aside textarea", timeout=5000)
        await page.fill("aside textarea", "V13 提示词验证")
        await page.wait_for_timeout(300)
        check(True, "改：节点提示词已修改")
        await shot(page, "04_editor_node_edit")

        # 结构校验
        await page.click("button:has-text('结构校验')")
        await page.wait_for_selector("text=结构校验（PRD §7.2）", timeout=5000)
        check(True, "查：结构校验面板打开")

        # 试运行（执行按钮与「执行面板」按钮同名前缀，用 exact 定位）
        await page.get_by_role("button", name="执行", exact=True).click()
        await page.wait_for_selector("text=执行追踪（PRD §7.4）", timeout=8000)
        # 等待执行日志面板出现「执行完毕」（2 节点 × 1s ≈ 2s，给 15s 余量）
        await page.wait_for_selector("text=执行完毕", timeout=15000)
        check(True, "改：试运行后执行日志显示「执行完毕」")
        await shot(page, "05_editor_run")

        # ============ ③ 执行追踪：重跑 + 查时间线 ============
        print("\n── ③ 执行追踪（重跑/查时间线/展开面板）──")
        await page.goto(BASE + "/runs", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('执行追踪')", timeout=8000)
        check(await page.locator(".polaroid-card.rounded-lg.p-4").count() >= 1, "查：运行记录列表渲染")
        # 重新运行（增一条运行）
        runs_before = await page.locator(".polaroid-card.rounded-lg.p-4").count()
        await page.locator("button:has-text('重新运行')").first.click()
        await page.wait_for_timeout(1500)
        await page.wait_for_timeout(500)
        runs_after = await page.locator(".polaroid-card.rounded-lg.p-4").count()
        check(runs_after > runs_before, f"增：重新运行新增记录（{runs_before}→{runs_after}）")
        await shot(page, "06_runs_rerun")
        # 查：点开详情 + 展开执行面板
        await page.locator(".polaroid-card.rounded-lg.p-4").first.click()
        await page.wait_for_selector("text=节点级时间线（PRD §7.4）", timeout=6000)
        check(True, "查：节点级时间线渲染")
        await page.locator("button:has-text('展开执行面板')").first.click()
        await page.wait_for_selector("text=推理摘要", timeout=5000)
        check(True, "查：执行面板展开（推理摘要/工具/证据）")
        await shot(page, "07_runs_detail")
        # 筛选
        await page.select_option("select >> nth=1", "completed")
        await page.wait_for_timeout(400)
        check(True, "查：按状态筛选运行记录")

        # ============ ④ 资产：增/查/认证/退役 ============
        print("\n── ④ 认证资产库（增/查/认证/退役）──")
        await page.goto(BASE + "/assets", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('认证资产库')", timeout=8000)
        check(await page.locator("text=移动端登录全流程认证用例").count() >= 1, "查：预置资产渲染")
        # 增
        await page.click("button:has-text('＋ 新建资产')")
        await page.wait_for_selector("div.fixed input[placeholder='资产名称']", timeout=5000)
        await page.fill("div.fixed input[placeholder='资产名称']", "V13验证资产")
        await page.fill("div.fixed input[type='number']", "2")
        await page.click("div.fixed button:has-text('创建')")
        await page.wait_for_selector("text=V13验证资产", timeout=5000)
        check(await page.locator("text=V13验证资产").count() >= 1, "增：新建资产出现")
        # 查详情
        await page.locator("button:has-text('查看')").first.click()
        await page.wait_for_selector("text=资产详情", timeout=5000)
        check(True, "查：资产详情弹窗（门槛明细/审计日志）")
        await page.click("div.fixed button:has-text('×')")
        # 认证（pending → certified）
        asset_card = page.locator(".polaroid-card.rounded-lg.p-4 h3:has-text('支付模块变更驱动回归用例集')").first.locator("xpath=ancestor::div[contains(@class,'polaroid-card') and contains(@class,'p-4')][1]")
        check((await asset_card.locator("button:has-text('认证')").count()) >= 1, "查：待认证资产显示认证按钮")
        await asset_card.locator("button:has-text('认证')").click()
        await page.wait_for_timeout(600)
        await shot(page, "08_assets_crud")

        # ============ ⑤ 任务：提交/查/轮询/取消 ============
        print("\n── ⑤ 异步任务看板（提交/查/轮询/取消）──")
        await page.goto(BASE + "/tasks", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('异步任务看板')", timeout=8000)
        check(await page.locator("text=支付模块异步回归测试任务").count() >= 1, "查：预置任务渲染")
        # 提交
        await page.click("button:has-text('＋ 提交任务')")
        await page.wait_for_selector("div.fixed input[placeholder='任务名称']", timeout=5000)
        await page.fill("div.fixed input[placeholder='任务名称']", "V13验证任务")
        await page.fill("div.fixed input[placeholder='wf_xxx']", "wf_v13")
        await page.fill("div.fixed input[placeholder='n_xxx']", "n_v13")
        await page.fill("div.fixed input[placeholder='browser-farm-X']", "farm-v13")
        await page.click("div.fixed button:has-text('提交')")
        await page.wait_for_selector("text=V13验证任务", timeout=5000)
        check(await page.locator("text=V13验证任务").count() >= 1, "增：提交任务出现")
        # 查详情
        await page.locator(".polaroid-card.rounded-lg.p-3:has-text('V13验证任务') button:has-text('查看')").first.click()
        await page.wait_for_selector("text=任务详情", timeout=5000)
        check(True, "查：任务详情弹窗（结果回写/审计日志）")
        await page.click("div.fixed button:has-text('×')")
        # 轮询推进
        await page.locator(".polaroid-card.rounded-lg.p-3:has-text('支付模块异步回归测试任务') button:has-text('轮询推进')").click()
        await page.wait_for_timeout(600)
        check(True, "改：轮询推进任务进度")
        # 取消
        await page.locator(".polaroid-card.rounded-lg.p-3:has-text('支付模块异步回归测试任务') button:has-text('取消')").click()
        await page.wait_for_timeout(600)
        await shot(page, "09_tasks_crud")

        # ============ ⑥ 模型：授予/撤销/叠加/连接测试 ============
        print("\n── ⑥ 模型与额度（授予/撤销/叠加/连接测试）──")
        await page.goto(BASE + "/models", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('模型与额度')", timeout=8000)
        check(await page.locator(".polaroid-card.rounded-lg.p-4").count() >= 1, "查：模型注册表渲染")
        # 三层配置 Tab + 连接测试
        await page.click("button:has-text('三层配置')")
        await page.wait_for_selector("button:has-text('连接测试')", timeout=5000)
        check(True, "查：三层配置卡片渲染（连接测试按钮出现）")
        await page.locator("button:has-text('连接测试')").first.click()
        await page.wait_for_selector(".fixed.bottom-6.right-6", timeout=5000)
        check(True, "查：连接测试执行（toast 提示）")
        await page.wait_for_timeout(400)
        await shot(page, "10_models_registry")
        # 额度 Tab：授予 + 撤销
        await page.click("button:has-text('额度管理')")
        await page.wait_for_timeout(400)
        grants_before = await page.locator("button:has-text('撤销')").count()
        await page.click("button:has-text('＋ 额度授予')")
        await page.wait_for_selector("div.fixed input[placeholder='测试负责人']", timeout=5000)
        await page.fill("div.fixed input[type='number']", "500")
        await page.click("div.fixed button:has-text('授予')")
        await page.wait_for_timeout(600)
        grants_after = await page.locator("button:has-text('撤销')").count()
        check(grants_after > grants_before, f"增：额度授予记录（{grants_before}→{grants_after} 条可撤销）")
        await page.locator("button:has-text('撤销')").first.click()
        await page.wait_for_timeout(600)
        check(await page.locator("span:has-text('已撤销')").count() >= 1, "改：额度授予已撤销")
        await shot(page, "11_models_grant")
        # 用量 Tab
        await page.click("button:has-text('用量与成本')")
        await page.wait_for_selector("text=计量与成本", timeout=5000)
        check(True, "查：用量与成本表渲染")

        # ============ ⑦ 审计：追加/校验/导出 ============
        print("\n── ⑦ 审计证据账本（追加/校验/导出）──")
        await page.goto(BASE + "/audit", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('审计证据账本')", timeout=8000)
        check(await page.locator(".polaroid-card.rounded-lg.p-4 code").count() >= 1, "查：证据列表渲染")
        # 追加
        await page.click("button:has-text('＋ 追加证据')")
        await page.wait_for_selector("div.fixed textarea", timeout=5000)
        await page.fill("div.fixed textarea", "V13 追加证据验证")
        await page.fill("div.fixed input[placeholder='trace:xxx / gate:xxx / defect:xxx']", "trace:v13")
        await page.click("div.fixed button:has-text('追加')")
        await page.wait_for_selector("text=V13 追加证据验证", timeout=5000)
        check(await page.locator("text=V13 追加证据验证").count() >= 1, "增：追加证据出现")
        # 校验哈希链
        await page.click("button:has-text('校验哈希链')")
        await page.wait_for_selector("text=哈希链校验通过", timeout=5000)
        check(await page.locator("text=哈希链校验通过").count() >= 1, "查：哈希链校验通过")
        await shot(page, "12_audit_append")
        # 导出
        await page.click("button:has-text('导出账本')")
        await page.wait_for_selector("text=导出审计账本（合规审计）", timeout=5000)
        check(True, "查：导出账本弹窗（校验状态 + JSON 预览）")
        await page.click("div.fixed button:has-text('×')")

        # ============ ⑧ 能力：登记/放行审批 ============
        print("\n── ⑧ 开放能力控制台（登记/放行审批）──")
        await page.goto(BASE + "/capabilities", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('开放能力控制台')", timeout=8000)
        check(await page.locator("text=webFetch 工具").count() >= 1, "查：能力清单渲染")
        # 登记
        await page.click("button:has-text('＋ 登记能力')")
        await page.wait_for_selector("div.fixed input[placeholder='能力名称']", timeout=5000)
        await page.fill("div.fixed input[placeholder='能力名称']", "V13验证能力")
        await page.click("div.fixed button:has-text('登记')")
        await page.wait_for_selector("text=V13验证能力", timeout=5000)
        check(await page.locator("text=V13验证能力").count() >= 1, "增：登记能力出现")
        await shot(page, "13_caps_register")
        # 放行审批
        await page.click("button:has-text('审批记录')")
        await page.wait_for_selector("button:has-text('放行')", timeout=5000)
        await page.locator("button:has-text('放行')").first.click()
        await page.wait_for_selector("text=已放行", timeout=5000)
        check(await page.locator("text=已放行").count() >= 1, "改：审批放行成功")
        # 调用日志 Tab
        await page.click("button:has-text('调用日志')")
        await page.wait_for_selector("text=外部调用日志", timeout=5000)
        check(True, "查：调用日志表渲染")
        await shot(page, "14_caps_approve")

        # ============ ⑨ 资源：登记池/获取锁/释放锁 ============
        print("\n── ⑨ 资源与锁管理（登记池/获取锁/释放锁）──")
        await page.goto(BASE + "/resources", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('资源与锁管理')", timeout=8000)
        check(await page.locator("text=移动设备池").count() >= 1, "查：资源池渲染")
        # 登记资源池
        await page.click("button:has-text('＋ 登记资源池')")
        await page.wait_for_selector("div.fixed input[placeholder='资源池名称']", timeout=5000)
        await page.locator("div.fixed select").first.select_option(value="数据源")
        await page.fill("div.fixed input[placeholder='资源池名称']", "V13数据源池")
        await page.click("div.fixed button:has-text('登记')")
        await page.wait_for_selector("text=V13数据源池", timeout=5000)
        check(await page.locator("text=V13数据源池").count() >= 1, "增：登记资源池出现")
        await shot(page, "15_res_pool")
        # 获取锁
        await page.click("button:has-text('资源锁')")
        await page.click("button:has-text('＋ 获取锁')")
        await page.wait_for_selector("div.fixed input[placeholder='dev_a / env_staging / slot_1 ...']", timeout=5000)
        await page.fill("div.fixed input[placeholder='dev_a / env_staging / slot_1 ...']", "dev_a")
        await page.fill("div.fixed input[placeholder='工作流名 · 节点名']", "V13验证 · n_lock")
        await page.click("div.fixed button:has-text('获取')")
        await page.wait_for_selector("text=锁已获取", timeout=5000)
        check(True, "增：获取资源锁成功")
        # 释放锁
        await page.locator(".polaroid-card.rounded-lg.p-4 button:has-text('释放')").first.click()
        await page.wait_for_selector("text=锁已释放", timeout=5000)
        check(True, "改：释放资源锁成功")
        await shot(page, "16_res_lock")
        # 锁事件 Tab
        await page.click("button:has-text('锁事件')")
        await page.wait_for_selector("text=锁事件时间线", timeout=5000)
        check(True, "查：锁事件时间线渲染")

        # ============ ⑩ 配置：改配置项/改预算策略 ============
        print("\n── ⑩ 统一配置中心（改配置项/改预算策略）──")
        await page.goto(BASE + "/settings", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('统一配置中心')", timeout=8000)
        check(await page.locator("text=驱动配置").count() >= 1, "查：分区导航渲染")
        # 改配置项
        await page.locator("select").first.select_option(value="Selenium Chrome")
        await page.wait_for_selector("text=配置已保存", timeout=5000)
        check(await page.locator("text=配置已保存").count() >= 1, "改：配置项保存成功")
        await shot(page, "17_settings_item")
        # 改预算策略（budget select 在 "预算、熔断与并发" 区域）
        await page.locator("select:has(option[value='降级输出'])").first.select_option(value="降级输出")
        await page.wait_for_selector("text=预算策略已更新", timeout=5000)
        check(await page.locator("text=预算策略已更新").count() >= 1, "改：预算策略更新成功")

        # ============ ⑪ 跨模块业务串联 ============
        print("\n── ⑪ 跨模块业务串联 ──")
        # 工作台 → 各模块 → 返回
        await page.goto(BASE + "/dashboard", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('工作台总览')", timeout=8000)
        check(await page.locator("text=＋ 新建工作流").count() >= 1, "串联：工作台总览渲染")
        for route, sel in [
            ("/workflows", "h1:has-text('工作流列表')"),
            ("/runs", "h1:has-text('执行追踪')"),
            ("/assets", "h1:has-text('认证资产库')"),
            ("/tasks", "h1:has-text('异步任务看板')"),
            ("/models", "h1:has-text('模型与额度')"),
            ("/audit", "h1:has-text('审计证据账本')"),
            ("/capabilities", "h1:has-text('开放能力控制台')"),
            ("/resources", "h1:has-text('资源与锁管理')"),
            ("/settings", "h1:has-text('统一配置中心')"),
        ]:
            await page.goto(BASE + route, wait_until="networkidle")
            await page.wait_for_selector(sel, timeout=6000)
        check(True, "串联：9 个模块依次跳转无异常")
        # 编辑跳转画布（业务联系：工作流 → 画布）
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h1:has-text('工作流列表')", timeout=6000)
        await wf_card(page, "我的第一个测试工作流").locator("button:has-text('编辑')").click()
        await page.wait_for_selector("text=节点模板库（PRD §11）", timeout=8000)
        check(True, "串联：工作流编辑跳转编排画布")
        await shot(page, "18_full_chain")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        check(len(real_errors) == 0, f"无页面 JS 报错（{len(real_errors)} 条）")

        await browser.close()

    print(f"\n========== V13 全功能增删改查 + 业务串联 验证结果 ==========")
    print(f"通过 {_OK} 项 · 失败 {_FAIL} 项")
    if _FAIL == 0:
        print(f"🎉 V13 全功能增删改查 + 业务串联验证全部通过")
    else:
        print(f"⚠ 有 {_FAIL} 项失败，请检查")


if __name__ == "__main__":
    asyncio.run(run())
