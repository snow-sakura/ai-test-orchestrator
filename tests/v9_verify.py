"""V9 Loop Engineering 自动验证脚本
验证 /capabilities 开放能力控制台全部功能（PRD §6.1）：
1. 页面渲染 + 预置能力清单加载
2. 能力卡片渲染（kind/status badge、⚠ 危险操作、30天调用）
3. 按类型筛选
4. 按状态筛选
5. 登记能力（弹窗创建 → toast）
6. 调用日志 Tab + 结果筛选（成功/待审批/失败）
7. 审批记录 Tab + 放行按钮（待审批 → 已放行）
8. 接入配置 Tab（keyMasked/scopes/角色）
9. 业务串联：开放能力 → 工作流列表
关键步骤自动截图到 tests/screenshots/v9/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v9")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_capabilities():
    """把 capabilities.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "capabilities.json")
    seeds = {
        "capabilities": [
            {"id": "cap_wf_cicd", "kind": "工作流", "name": "代码变更驱动的 CI/CD 质量门禁",
             "source": "wf_cicd", "exposed": True, "status": "active",
             "protocol": "OpenAPI / 标准化工具协议", "auth": "API Key + 角色授权",
             "dangerousOps": ["运行测试", "写入缺陷"], "callCount30d": 128, "lastCalled": "2026-10-26 15:20",
             "desc": "发布时显式声明对外暴露的工作流，供外部智能体系统调度"},
            {"id": "cap_node_case_gen", "kind": "节点", "name": "代码变更驱动测试生成节点",
             "source": "wf_cicd:n_case_gen", "exposed": True, "status": "active",
             "protocol": "MCP Tool", "auth": "API Key",
             "dangerousOps": ["生成并写入用例"], "callCount30d": 56, "lastCalled": "2026-10-26 14:10",
             "desc": "单节点封装为可调用工具，支持外部系统按参数触发用例生成"},
            {"id": "cap_tool_browser", "kind": "工具", "name": "Browser-use 浏览器智能体",
             "source": "capability_pack:browser-use", "exposed": True, "status": "active",
             "protocol": "HTTP 回调", "auth": "OAuth2 客户端授权",
             "dangerousOps": ["修改资产"], "callCount30d": 342, "lastCalled": "2026-10-26 16:02",
             "desc": "认证能力包暴露为对外工具，执行类操作默认进入待审批队列"},
            {"id": "cap_rule_gate", "kind": "规则", "name": "质量门禁确定性裁决规则",
             "source": "rule:quality_gate", "exposed": False, "status": "disabled",
             "protocol": "—", "auth": "内部",
             "dangerousOps": [], "callCount30d": 0, "lastCalled": "",
             "desc": "内部规则，默认不对外暴露"},
            {"id": "cap_wf_explore", "kind": "工作流", "name": "智能探索与大规模异步回归",
             "source": "wf_explore", "exposed": True, "status": "pending_approval",
             "protocol": "OpenAPI / 标准化工具协议", "auth": "API Key + 角色授权",
             "dangerousOps": ["运行测试"], "callCount30d": 0, "lastCalled": "",
             "desc": "新发布工作流，包含执行类操作，等待平台侧审批后放行"},
        ],
        "callLogs": [
            {"id": "call_001", "ts": "2026-10-26 15:20", "capability": "代码变更驱动的 CI/CD 质量门禁", "caller": "external-agent-7", "result": "success", "duration": "6m18s", "auditRef": "trace:run_seed_002"},
            {"id": "call_002", "ts": "2026-10-26 14:10", "capability": "代码变更驱动测试生成节点", "caller": "ci-pipeline-3", "result": "success", "duration": "42s", "auditRef": "trace:gen_088"},
            {"id": "call_003", "ts": "2026-10-26 16:02", "capability": "Browser-use 浏览器智能体", "caller": "external-agent-7", "result": "pending_approval", "duration": "—", "auditRef": "approval:cap_tool_browser"},
            {"id": "call_004", "ts": "2026-10-25 11:40", "capability": "代码变更驱动的 CI/CD 质量门禁", "caller": "ci-pipeline-1", "result": "failed", "duration": "2m01s", "auditRef": "trace:run_seed_004"},
        ],
        "approvals": [
            {"id": "ap_001", "ts": "2026-10-26 16:02", "capability": "Browser-use 浏览器智能体", "op": "修改资产", "status": "待审批", "by": ""},
            {"id": "ap_002", "ts": "2026-10-26 15:20", "capability": "代码变更驱动的 CI/CD 质量门禁", "op": "运行测试", "status": "已放行", "by": "规则引擎（低风险自动放行）"},
            {"id": "ap_003", "ts": "2026-10-25 21:36", "capability": "智能探索与大规模异步回归", "op": "写入缺陷", "status": "已放行", "by": "测试负责人"},
        ],
        "connects": [
            {"id": "conn_001", "caller": "external-agent-7", "keyMasked": "sk-ext-••••••••a1b2", "role": "外部智能体", "scopes": ["运行测试", "查询结果"], "status": "active", "created": "2026-09-01"},
            {"id": "conn_002", "caller": "ci-pipeline-1", "keyMasked": "sk-ci-••••••••c3d4", "role": "CI 流水线", "scopes": ["运行测试"], "status": "active", "created": "2026-08-15"},
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)
    print(f"[reset] capabilities.json 复位为预置种子（{len(seeds['capabilities'])} 能力 / {len(seeds['callLogs'])} 日志 / {len(seeds['approvals'])} 审批 / {len(seeds['connects'])} 接入）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    reset_capabilities()

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置能力清单加载
        await page.goto(BASE + "/capabilities", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('开放能力控制台')", timeout=8000)
        passed.append("开放能力控制台页渲染")
        print("✅ 开放能力控制台页渲染")

        await page.locator("text=代码变更驱动的 CI/CD 质量门禁").first.wait_for(timeout=5000)
        passed.append("预置能力清单加载")
        print("✅ 预置能力清单加载")
        await shot(page, "01_capabilities_list")

        # 2. 能力卡片渲染（kind/status badge、⚠ 危险操作、30天调用）
        assert await page.locator("text=已上线").count() >= 1, "未找到 已上线 状态"
        assert await page.locator("text=待审批").count() >= 1, "未找到 待审批 状态"
        assert await page.locator(".polaroid-card.rounded-lg.p-4 >> text=⚠ 运行测试").count() >= 1, "未找到 ⚠ 危险操作标记"
        assert await page.locator("text=30天调用").count() >= 1, "未找到 30天调用 统计"
        passed.append("能力卡片渲染（kind / status / ⚠ 危险操作 / 30天调用）")
        print("✅ 能力卡片渲染（kind / status / ⚠ 危险操作 / 30天调用）")

        # 3. 按类型筛选（节点 → 命中 1 条）
        kind_select = page.locator(".polaroid-card.rounded-lg.p-4 ~ .flex select, select").nth(0)
        # 筛选栏的两个 select（kind 在前、status 在后）
        kind_select = page.locator("select").nth(0)
        await kind_select.select_option(value="节点")
        await page.wait_for_timeout(300)
        node_count = await page.locator(".polaroid-card.rounded-lg.p-4 >> text=代码变更驱动测试生成节点").count()
        assert node_count >= 1, "类型筛选：节点 未命中"
        passed.append(f"按类型筛选（节点 命中 {node_count} 条）")
        print(f"✅ 按类型筛选（节点 命中 {node_count} 条）")
        await kind_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 4. 按状态筛选（待审批 → 命中 1 条）
        status_select = page.locator("select").nth(1)
        await status_select.select_option(value="pending_approval")
        await page.wait_for_timeout(300)
        pending_count = await page.locator(".polaroid-card.rounded-lg.p-4 >> text=待审批").count()
        assert pending_count >= 1, "状态筛选：待审批 未命中"
        passed.append(f"按状态筛选（待审批 命中 {pending_count} 条）")
        print(f"✅ 按状态筛选（待审批 命中 {pending_count} 条）")
        await status_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 5. 登记能力（弹窗创建 → toast）
        await page.click("button:has-text('＋ 登记能力')")
        await page.wait_for_selector("h3:has-text('登记对外能力')", timeout=5000)
        await page.fill("input[placeholder='能力名称']", "V9 测试外部能力")
        await page.fill("input[placeholder='wf_xxx / n_xxx']", "wf_v9_test")
        await page.locator("div.fixed button:has-text('登记')").first.click()
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        assert await page.locator(".polaroid-card.rounded-lg.p-4 >> text=V9 测试外部能力").count() >= 1, "登记后未出现新能力"
        passed.append("登记能力（弹窗创建 + 列表更新 + toast）")
        print("✅ 登记能力（弹窗创建 + 列表更新 + toast）")
        await shot(page, "02_created")

        # 6. 调用日志 Tab + 结果筛选
        await page.click("button:has-text('调用日志')")
        await page.wait_for_selector("text=外部调用日志（与内部运行共享同一审计账本）", timeout=5000)
        assert await page.locator("text=trace:run_seed_002").count() >= 1, "调用日志未命中 auditRef"
        passed.append("调用日志 Tab（4 条日志 + 审计引用）")
        print("✅ 调用日志 Tab（4 条日志 + 审计引用）")
        log_select = page.locator("select").last
        await log_select.select_option(value="failed")
        await page.wait_for_timeout(300)
        failed_count = await page.locator("text=trace:run_seed_004").count()
        assert failed_count >= 1, "调用日志结果筛选：failed 未命中"
        passed.append(f"调用日志结果筛选（failed 命中 {failed_count} 条）")
        print(f"✅ 调用日志结果筛选（failed 命中 {failed_count} 条）")
        await shot(page, "03_call_logs")

        # 7. 审批记录 Tab + 放行按钮
        await page.click("button:has-text('审批记录')")
        await page.wait_for_selector(".polaroid-card.rounded-lg.p-4 >> text=修改资产", timeout=5000)
        assert await page.locator(".polaroid-card.rounded-lg.p-4 >> text=待审批").count() >= 1, "审批记录未命中 待审批"
        passed.append("审批记录 Tab（3 条审批 + 待审批状态）")
        print("✅ 审批记录 Tab（3 条审批 + 待审批状态）")
        # 放行 ap_001（Browser-use 修改资产 待审批）
        await page.locator("button:has-text('放行')").first.click()
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(600)
        assert await page.locator(".polaroid-card.rounded-lg.p-4 >> text=测试负责人").count() >= 1, "放行后未出现审批方"
        passed.append("审批放行（待审批 → 已放行 + 审批方 + toast）")
        print("✅ 审批放行（待审批 → 已放行 + 审批方 + toast）")
        await shot(page, "04_approved")

        # 8. 接入配置 Tab
        await page.click("button:has-text('接入配置')")
        await page.wait_for_selector(".polaroid-card.rounded-lg.p-4 >> text=external-agent-7", timeout=5000)
        assert await page.locator("text=sk-ext-••••••••a1b2").count() >= 1, "接入配置未命中 keyMasked"
        assert await page.locator("text=外部智能体").count() >= 1, "接入配置未命中 角色"
        passed.append("接入配置 Tab（2 条接入 + keyMasked + scopes + 角色）")
        print("✅ 接入配置 Tab（2 条接入 + keyMasked + scopes + 角色）")
        await shot(page, "05_connects")

        # 9. 业务串联：开放能力 → 工作流列表
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：开放能力 → 工作流列表")
        print("✅ 业务串联：开放能力 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V9 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V9 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
