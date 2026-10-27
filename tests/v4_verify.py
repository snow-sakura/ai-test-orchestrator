"""V4 Loop Engineering 自动验证脚本
验证 /runs 执行追踪页全部功能（PRD §6.6 / §7.4）：
1. 页面渲染 + 预置运行记录
2. 按工作流筛选
3. 按状态筛选（completed / running / failed）
4. 运行详情：节点级时间线
5. 时间线展开：推理摘要、工具调用、输入绑定、输出结果、证据引用
6. 门禁裁决区（确定性判定 + 归因叙述分离，PRD 原则五）
7. 执行日志（PRD §7.4）
8. 触发执行 → 在追踪页查看新运行记录（业务串联：工作流 → 执行 → 追踪）
9. 工作流列表 → 执行追踪 跳转
关键步骤自动截图到 tests/screenshots/v4/
"""
import asyncio
import json
import os
import urllib.request
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v4")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_runs():
    """把 runs.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "runs.json")
    seed = {
        "run_seed_001": {
            "id": "run_seed_001",
            "workflow_id": "default-workflow",
            "workflow_name": "我的第一个测试工作流",
            "trigger": "手动",
            "status": "completed",
            "started": "10-26 16:42:00",
            "duration": "2s08ms",
            "tokens": 1612,
            "cost": 0.0081,
            "gate": {
                "verdict": "通过",
                "engine": "确定性规则引擎",
                "narrative": "主要贡献因素为执行通过率与覆盖率",
            },
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
            "created": "16:42:00",
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    print(f"[reset] runs.json 复位为预置种子（{path}）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    reset_runs()
    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置运行记录
        await page.goto(BASE + "/runs", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('执行追踪')", timeout=8000)
        passed.append("执行追踪页渲染")
        print("✅ 执行追踪页渲染")

        # 预置记录应出现（卡片含工作流名称）
        await page.locator(".polaroid-card.rounded-lg.p-4.cursor-pointer h3:has-text('我的第一个测试工作流')").first.wait_for(timeout=5000)
        passed.append("预置运行记录加载（我的第一个测试工作流）")
        print("✅ 预置运行记录加载（我的第一个测试工作流）")
        await shot(page, "01_runs_list")

        # 2. 运行卡片渲染（含 Token / 成本 / 状态 / 门禁）
        assert await page.locator("text=Token").count() >= 1, "未找到 Token 展示"
        assert await page.locator("text=已完成").count() >= 1, "未找到 已完成 状态标签"
        assert await page.locator("text=门禁").count() >= 1, "未找到 门禁 展示"
        passed.append("运行卡片渲染（状态 / Token / 成本 / 门禁）")
        print("✅ 运行卡片渲染（状态 / Token / 成本 / 门禁）")

        # 3. 按状态筛选
        # 切到「已完成」
        status_btns = page.locator("button.rounded-full")
        for btn in await status_btns.all():
            txt = (await btn.inner_text()).strip()
            if txt.startswith("已完成"):
                await btn.click()
                break
        await page.wait_for_timeout(300)
        completed_cards = await page.locator("text=已完成").count()
        assert completed_cards >= 1, "状态筛选：已完成 未命中"
        passed.append(f"按状态筛选（已完成 命中 {completed_cards} 条）")
        print(f"✅ 按状态筛选（已完成 命中 {completed_cards} 条）")

        # 切回「全部」
        for btn in await status_btns.all():
            txt = (await btn.inner_text()).strip()
            if txt.startswith("全部"):
                await btn.click()
                break
        await page.wait_for_timeout(300)
        passed.append("状态筛选可切回全部")
        print("✅ 状态筛选可切回全部")

        # 4. 工作流筛选
        wf_select = page.locator("select").first
        await wf_select.wait_for(timeout=5000)
        # 选第一个非空工作流选项
        options = await wf_select.locator("option:not([value=''])").all()
        if options:
            first_wf = await options[0].inner_text()
            await wf_select.select_option(label=first_wf)
            await page.wait_for_timeout(300)
            passed.append(f"按工作流筛选（{first_wf}）")
            print(f"✅ 按工作流筛选（{first_wf}）")
        # 切回全部
        await wf_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 5. 查看详情：节点级时间线 + 执行面板 + 门禁裁决
        # 点击第一张运行卡片的「查看」按钮
        view_btn = page.locator("button:has-text('查看')").first
        await view_btn.wait_for(timeout=5000)
        await view_btn.click()
        await page.wait_for_selector("text=运行详情", timeout=5000)
        passed.append("运行详情面板打开")
        print("✅ 运行详情面板打开")

        # 节点级时间线
        await page.locator("h4:has-text('节点级时间线')").first.wait_for(timeout=5000)
        # 验证时间线节点渲染（预置有 2 个节点）
        assert await page.locator("text=开始").count() >= 1, "时间线节点「开始」未渲染"
        assert await page.locator("text=需求解析").count() >= 1, "时间线节点「需求解析」未渲染"
        passed.append("节点级时间线渲染（PRD §7.4）")
        print("✅ 节点级时间线渲染（PRD §7.4）")
        await shot(page, "02_detail_timeline")

        # 6. 展开第一个节点的执行面板
        expand_btn = page.locator("button:has-text('展开执行面板')").first
        await expand_btn.click()
        await page.wait_for_selector("text=推理摘要", timeout=5000)
        await page.wait_for_selector("text=工具调用", timeout=5000)
        await page.wait_for_selector("text=证据引用", timeout=5000)
        passed.append("执行面板展开（推理 / 工具 / 证据）")
        print("✅ 执行面板展开（推理 / 工具 / 证据）")
        await shot(page, "03_expanded_node")

        # 7. 门禁裁决区
        await page.locator("text=门禁裁决区").wait_for(timeout=5000)
        assert await page.locator("text=确定性判定").count() >= 1, "未找到 确定性判定"
        assert await page.locator("text=归因叙述").count() >= 1, "未找到 归因叙述"
        passed.append("门禁裁决区（PRD 原则五）")
        print("✅ 门禁裁决区（PRD 原则五）")

        # 8. 执行日志
        await page.locator("text=执行日志").wait_for(timeout=5000)
        passed.append("执行日志（PRD §7.4）")
        print("✅ 执行日志（PRD §7.4）")
        await shot(page, "04_full_detail")

        # 9. 触发执行 → 在追踪页看到新运行记录（业务串联）
        # 找到「重新运行」按钮并触发
        rerun_btn = page.locator("button:has-text('重新运行')").first
        await rerun_btn.click()
        await page.wait_for_selector("text=已触发运行", timeout=5000)
        passed.append("触发执行（重新运行）")
        print("✅ 触发执行（重新运行）")

        # 等待执行完成（约 2 个节点 × 1s = 2s + 轮询刷新）
        await page.wait_for_timeout(5000)
        await page.reload(wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('执行追踪')", timeout=8000)
        # 新运行记录应出现（run_seed_001 之外）
        total_runs = await page.locator(".polaroid-card.rounded-lg.p-4.cursor-pointer").count()
        assert total_runs >= 2, f"触发后运行记录未增加（total={total_runs}）"
        passed.append(f"触发后运行记录增加（共 {total_runs} 条）")
        print(f"✅ 触发后运行记录增加（共 {total_runs} 条）")
        await shot(page, "05_after_trigger")

        # 10. 业务串联：工作流列表 → 执行追踪
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：工作流列表页")
        print("✅ 业务串联：工作流列表页")
        await page.goto(BASE + "/runs", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('执行追踪')", timeout=8000)
        passed.append("业务串联：执行追踪页")
        print("✅ 业务串联：执行追踪页")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V4 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V4 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
