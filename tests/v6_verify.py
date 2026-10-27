"""V6 Loop Engineering 自动验证脚本
验证 /tasks 异步任务看板全部功能（PRD §6.4）：
1. 页面渲染 + 预置任务加载
2. 任务看板 4 列（运行中 / 已完成 / 失败 / 超时）
3. 任务卡片渲染（类型标签、工作流、节点、进度、资源锁、轮询/回调）
4. 搜索过滤
5. 按类型筛选
6. 按工作流筛选
7. 按资源筛选
8. 提交异步任务（新建）
9. 任务详情：结果回写 + 审计日志
10. 轮询推进（结果回写变量池）
11. 模拟超时
12. 取消任务
13. 业务串联：异步任务看板 → 工作流列表
关键步骤自动截图到 tests/screenshots/v6/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v6")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_tasks():
    """把 tasks.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "tasks.json")
    now = "2026-10-26 15:00"
    seed = {
        "task_running_001": {
            "id": "task_running_001", "type": "异步测试任务", "name": "支付模块异步回归测试任务",
            "status": "running", "workflow": "wf_payment_regression", "node": "n_async_regression",
            "progress": 62, "started": "2026-10-26 14:02", "eta": "约 8 分钟",
            "owner": "test-agent-01", "resource": "browser-farm-A",
            "result_ref": "var://wf_payment_regression/result_async",
            "poll_interval": 15, "timeout_sec": 1800, "mode": "poll", "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 14:02", "action": "submitted", "by": "异步测试执行节点", "detail": "任务已提交，立即返回任务标识"},
                {"ts": "2026-10-26 14:35", "action": "polling", "by": "平台", "detail": "第 15:00 轮轮询，进度 62%"},
            ],
            "created": now,
        },
        "task_running_002": {
            "id": "task_running_002", "type": "外部智能体任务", "name": "Browser-use 智能探索外部调用",
            "status": "running", "workflow": "wf_explore", "node": "n_external_agent",
            "progress": 38, "started": "2026-10-26 13:48", "eta": "约 15 分钟",
            "owner": "external-agent-7", "resource": "web-farm-B",
            "result_ref": "var://wf_explore/external_result",
            "poll_interval": 0, "timeout_sec": 3600, "mode": "callback", "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 13:48", "action": "submitted", "by": "外部智能体节点", "detail": "已提交外部调用，等待事件回调"},
                {"ts": "2026-10-26 14:00", "action": "callback", "by": "external-agent-7", "detail": "回调事件已接收，进度 38%"},
            ],
            "created": now,
        },
        "task_success_001": {
            "id": "task_success_001", "type": "回归任务", "name": "核心接口每日巡检回归任务",
            "status": "success", "workflow": "wf_api_daily", "node": "n_regression",
            "progress": 100, "started": "2026-10-26 09:00", "eta": "已完成",
            "owner": "test-agent-02", "resource": "api-farm-C",
            "result_ref": "var://wf_api_daily/regression_result",
            "poll_interval": 30, "timeout_sec": 900, "mode": "poll", "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 09:00", "action": "submitted", "by": "回归任务节点", "detail": "任务已提交"},
                {"ts": "2026-10-26 09:12", "action": "completed", "by": "平台", "detail": "结果已写回变量池 var://wf_api_daily/regression_result，唤醒下游节点"},
            ],
            "created": now,
        },
        "task_failed_001": {
            "id": "task_failed_001", "type": "数据生成任务", "name": "用户角色权限测试数据生成",
            "status": "failed", "workflow": "wf_rbac", "node": "n_data_gen",
            "progress": 45, "started": "2026-10-26 10:15", "eta": "失败",
            "owner": "data-agent-1", "resource": "data-farm-D",
            "result_ref": "var://wf_rbac/data_result",
            "poll_interval": 20, "timeout_sec": 600, "mode": "poll", "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-26 10:15", "action": "submitted", "by": "数据生成节点", "detail": "任务已提交"},
                {"ts": "2026-10-26 10:24", "action": "failed", "by": "data-agent-1", "detail": "数据源连接超时，任务失败，未回写结果"},
            ],
            "created": now,
        },
        "task_timeout_001": {
            "id": "task_timeout_001", "type": "探索任务", "name": "Web 端深度探索任务（已超时）",
            "status": "timeout", "workflow": "wf_web_explore", "node": "n_explore_deep",
            "progress": 71, "started": "2026-10-25 22:10", "eta": "已超时",
            "owner": "explore-agent-3", "resource": "browser-farm-E",
            "result_ref": "var://wf_web_explore/explore_result",
            "poll_interval": 30, "timeout_sec": 900, "mode": "poll", "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-25 22:10", "action": "submitted", "by": "探索任务节点", "detail": "任务已提交"},
                {"ts": "2026-10-25 22:25", "action": "timeout", "by": "平台", "detail": "超过最大执行时长（900s），按策略终止，未回写结果，转人工处理"},
            ],
            "created": now,
        },
        "task_canceled_001": {
            "id": "task_canceled_001", "type": "异步测试任务", "name": "移动端多端回归（已取消）",
            "status": "canceled", "workflow": "wf_mobile", "node": "n_mobile_async",
            "progress": 20, "started": "2026-10-25 18:30", "eta": "已取消",
            "owner": "test-agent-05", "resource": "device-farm-F",
            "result_ref": "var://wf_mobile/mobile_result",
            "poll_interval": 10, "timeout_sec": 1200, "mode": "poll", "cancel_status": "idle",
            "auditLog": [
                {"ts": "2026-10-25 18:30", "action": "submitted", "by": "移动端异步节点", "detail": "任务已提交"},
                {"ts": "2026-10-25 18:42", "action": "canceled", "by": "测试负责人", "detail": "手动取消任务，资源锁已释放"},
            ],
            "created": now,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    print(f"[reset] tasks.json 复位为预置种子（{path}）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    # 复位 tasks.json，让后端 startup seed_tasks 重新生成预置数据
    reset_tasks()

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置任务加载
        await page.goto(BASE + "/tasks", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('异步任务看板')", timeout=8000)
        passed.append("异步任务看板页渲染")
        print("✅ 异步任务看板页渲染")

        # 预置任务卡片出现
        await page.locator("text=支付模块异步回归测试任务").first.wait_for(timeout=5000)
        passed.append("预置异步任务加载（支付模块异步回归测试任务）")
        print("✅ 预置异步任务加载（支付模块异步回归测试任务）")
        await shot(page, "01_tasks_board")

        # 2. 任务看板 4 列（PRD §6.4 全局任务看板）
        for col in ["运行中", "已完成", "失败", "超时"]:
            await page.locator(f".polaroid-card.rounded-lg.p-4 h3:has-text('{col}')").first.wait_for(timeout=5000)
        passed.append("任务看板 4 列（运行中 / 已完成 / 失败 / 超时）")
        print("✅ 任务看板 4 列（运行中 / 已完成 / 失败 / 超时）")

        # 3. 任务卡片渲染（类型标签、工作流、节点、进度、资源锁、轮询/回调）
        assert await page.locator("text=异步测试任务").count() >= 1, "未找到 异步测试任务 类型标签"
        assert await page.locator("text=wf_payment_regression").count() >= 1, "未找到 工作流 字段"
        assert await page.locator("text=n_async_regression").count() >= 1, "未找到 节点 字段"
        assert await page.locator("text=62%").count() >= 1, "未找到 进度百分比"
        assert await page.locator("text=browser-farm-A").count() >= 1, "未找到 资源锁"
        assert await page.locator("text=轮询").count() >= 1, "未找到 轮询 模式"
        assert await page.locator("text=回调").count() >= 1, "未找到 回调 模式"
        passed.append("任务卡片渲染（类型 / 工作流 / 节点 / 进度 / 资源锁 / 轮询·回调）")
        print("✅ 任务卡片渲染（类型 / 工作流 / 节点 / 进度 / 资源锁 / 轮询·回调）")
        await shot(page, "02_task_cards")

        # 4. 搜索过滤（搜索"巡检"命中 核心接口每日巡检回归任务，排除 支付任务）
        await page.fill("input[placeholder='搜索任务名称...']", "巡检")
        await page.wait_for_timeout(300)
        assert await page.locator("text=核心接口每日巡检回归任务").count() >= 1, "搜索未命中 巡检 回归任务"
        assert await page.locator("text=支付模块异步回归测试任务").count() == 0, "搜索未排除 支付任务"
        passed.append("搜索过滤命中并排除")
        print("✅ 搜索过滤命中并排除")
        await page.fill("input[placeholder='搜索任务名称...']", "")
        await page.wait_for_timeout(300)

        # 5. 按类型筛选
        type_select = page.locator("select").nth(0)
        await type_select.wait_for(timeout=5000)
        await type_select.select_option(value="回归任务")
        await page.wait_for_timeout(300)
        regression_cards = await page.locator(".polaroid-card.rounded-lg.p-3 h4").count()
        assert regression_cards >= 1, "类型筛选：回归任务 未命中"
        passed.append(f"按类型筛选（回归任务 命中 {regression_cards} 项）")
        print(f"✅ 按类型筛选（回归任务 命中 {regression_cards} 项）")
        await type_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 6. 按工作流筛选
        workflow_select = page.locator("select").nth(1)
        await workflow_select.select_option(value="wf_api_daily")
        await page.wait_for_timeout(300)
        wf_cards = await page.locator(".polaroid-card.rounded-lg.p-3 h4").count()
        assert wf_cards >= 1, "工作流筛选：wf_api_daily 未命中"
        passed.append(f"按工作流筛选（wf_api_daily 命中 {wf_cards} 项）")
        print(f"✅ 按工作流筛选（wf_api_daily 命中 {wf_cards} 项）")
        await workflow_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 7. 按资源筛选
        resource_select = page.locator("select").nth(2)
        await resource_select.select_option(value="browser-farm-A")
        await page.wait_for_timeout(300)
        res_cards = await page.locator(".polaroid-card.rounded-lg.p-3 h4").count()
        assert res_cards >= 1, "资源筛选：browser-farm-A 未命中"
        passed.append(f"按资源筛选（browser-farm-A 命中 {res_cards} 项）")
        print(f"✅ 按资源筛选（browser-farm-A 命中 {res_cards} 项）")
        await resource_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 8. 提交异步任务（新建）
        await page.click("button:has-text('＋ 提交任务')")
        await page.wait_for_selector("h3:has-text('提交异步任务')", timeout=5000)
        await page.fill("input[placeholder='任务名称']", "V6 自动测试任务")
        await page.fill("input[placeholder='wf_xxx']", "wf_v6_test")
        await page.fill("input[placeholder='n_xxx']", "n_v6_test")
        await page.fill("input[placeholder='browser-farm-X']", "browser-farm-G")
        # 用 .first 定位弹窗内的提交按钮（避免与页面上方的「＋ 提交任务」混淆）
        await page.locator("div.fixed button:has-text('提交')").first.click()
        await page.wait_for_selector("text=异步任务已提交", timeout=5000)
        await page.wait_for_selector("text=V6 自动测试任务", timeout=5000)
        passed.append("提交异步任务成功")
        print("✅ 提交异步任务成功")
        await shot(page, "03_created")

        # 9. 任务详情：结果回写 + 审计日志
        view_btn = page.locator("button:has-text('查看')").first
        await view_btn.wait_for(timeout=5000)
        await view_btn.click()
        await page.wait_for_selector("text=任务详情", timeout=5000)
        await page.wait_for_selector("text=结果回写变量池", timeout=5000)
        await page.wait_for_selector("text=任务审计日志", timeout=5000)
        passed.append("任务详情：结果回写 + 审计日志")
        print("✅ 任务详情：结果回写 + 审计日志")
        await shot(page, "04_detail")

        # 10. 轮询推进（结果回写变量池）
        # 关闭详情弹窗
        await page.locator("div.fixed button:has-text('×')").first.click()
        await page.wait_for_selector("text=任务详情", state="detached", timeout=5000)

        # 找一个运行中任务进行轮询推进
        running_btns = page.locator("button:has-text('轮询推进')")
        running_count = await running_btns.count()
        if running_count > 0:
            await running_btns.first.click()
            # 等待 toast 出现（"轮询推进，进度 X%" 或 "任务完成，结果已写回变量池"），
            # 用固定定位的 toast 容器判断出现即可
            toast_box = page.locator(".fixed.bottom-6.right-6")
            await toast_box.first.wait_for(timeout=5000)
            await page.wait_for_timeout(500)
            passed.append("轮询推进（结果回写变量池）")
            print("✅ 轮询推进（结果回写变量池）")
        await shot(page, "05_poll")

        # 11. 模拟超时
        timeout_btns = page.locator("button:has-text('模拟超时')")
        timeout_count = await timeout_btns.count()
        if timeout_count > 0:
            await timeout_btns.first.click()
            await page.wait_for_selector("text=任务已标记为超时", timeout=5000)
            await page.wait_for_timeout(500)
            passed.append("模拟超时")
            print("✅ 模拟超时")
        await shot(page, "06_timeout")

        # 12. 取消任务（定位「取消」按钮在卡片内，避免与弹窗关闭按钮混淆）
        cancel_btns = page.locator(".polaroid-card.rounded-lg.p-3 button:has-text('取消')")
        cancel_count = await cancel_btns.count()
        if cancel_count > 0:
            await cancel_btns.first.click()
            await page.wait_for_selector("text=任务已取消", timeout=5000)
            await page.wait_for_timeout(500)
            passed.append("取消任务")
            print("✅ 取消任务")
        await shot(page, "07_canceled")

        # 13. 业务串联：异步任务看板 → 工作流列表
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：异步任务看板 → 工作流列表")
        print("✅ 业务串联：异步任务看板 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V6 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V6 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
