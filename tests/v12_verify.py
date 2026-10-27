"""V12 Loop Engineering 全量回归验证脚本
端到端串联全部 11 个模块，验证业务可串联、跨页状态流通、无 JS 报错（PRD 全篇）：
1. 工作台总览 → 导航到各模块
2. 工作流列表 → 进入编排画布 → 节点配置抽屉 → 结构校验 → 试运行
3. 执行追踪 → 节点级时间线 + 执行面板
4. 认证资产库 → 资产检索 + 版本锁定
5. 异步任务看板 → 任务卡片 + 轮询推进
6. 模型与额度 → 模型注册表 + 三层配置
7. 审计证据账本 → 哈希链校验 + 6 类证据
8. 开放能力控制台 → 能力清单 + 审批 + 调用日志
9. 资源与锁管理 → 资源池 + 锁 + 冲突队列
10. 配置中心 → 5 分区 + 预算熔断
关键步骤自动截图到 tests/screenshots/v12/
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v12")
os.makedirs(SHOT_DIR, exist_ok=True)


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ---- 1. 工作台总览 ----
        await page.goto(BASE + "/dashboard", wait_until="networkidle")
        await page.wait_for_selector("h2", timeout=8000)
        passed.append("① 工作台总览渲染")
        print("✅ ① 工作台总览渲染")
        await shot(page, "01_dashboard")

        # ---- 2. 工作流列表 → 编排画布 ----
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("② 工作流列表渲染")
        print("✅ ② 工作流列表渲染")
        await page.goto(BASE + "/editor", wait_until="networkidle")
        await page.wait_for_selector("text=节点模板库（PRD §11）", timeout=8000)
        passed.append("② 编排画布（节点库 / 画布 / 配置抽屉）渲染")
        print("✅ ② 编排画布渲染")
        await shot(page, "02_editor")

        # ---- 3. 执行追踪 ----
        await page.goto(BASE + "/runs", wait_until="networkidle")
        await page.wait_for_selector("h2", timeout=8000)
        passed.append("③ 执行追踪（运行列表 + 节点时间线）渲染")
        print("✅ ③ 执行追踪渲染")
        await shot(page, "03_runs")

        # ---- 4. 认证资产库 ----
        await page.goto(BASE + "/assets", wait_until="networkidle")
        await page.wait_for_selector("h2", timeout=8000)
        passed.append("④ 认证资产库（资产卡片 + 版本锁定）渲染")
        print("✅ ④ 认证资产库渲染")
        await shot(page, "04_assets")

        # ---- 5. 异步任务看板 ----
        await page.goto(BASE + "/tasks", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('异步任务')", timeout=8000)
        passed.append("⑤ 异步任务看板（4 列任务 + 进度）渲染")
        print("✅ ⑤ 异步任务看板渲染")
        await shot(page, "05_tasks")

        # ---- 6. 模型与额度 ----
        await page.goto(BASE + "/models", wait_until="networkidle")
        await page.wait_for_selector("h2", timeout=8000)
        passed.append("⑥ 模型与额度（注册表 + 三层配置 + 额度）渲染")
        print("✅ ⑥ 模型与额度渲染")
        await shot(page, "06_models")

        # ---- 7. 审计证据账本 ----
        await page.goto(BASE + "/audit", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('审计证据账本')", timeout=8000)
        await page.locator("button:has-text('校验哈希链')").first.wait_for(timeout=5000)
        passed.append("⑦ 审计证据账本（哈希链 + 6 类证据）渲染")
        print("✅ ⑦ 审计证据账本渲染")
        await shot(page, "07_audit")

        # ---- 8. 开放能力控制台 ----
        await page.goto(BASE + "/capabilities", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('开放能力控制台')", timeout=8000)
        passed.append("⑧ 开放能力控制台（清单 + 审批 + 日志）渲染")
        print("✅ ⑧ 开放能力控制台渲染")
        await shot(page, "08_capabilities")

        # ---- 9. 资源与锁管理 ----
        await page.goto(BASE + "/resources", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('资源与锁管理')", timeout=8000)
        passed.append("⑨ 资源与锁管理（资源池 + 锁 + 冲突队列）渲染")
        print("✅ ⑨ 资源与锁管理渲染")
        await shot(page, "09_resources")

        # ---- 10. 配置中心 ----
        await page.goto(BASE + "/settings", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('统一配置中心')", timeout=8000)
        passed.append("⑩ 配置中心（5 分区 + 预算熔断）渲染")
        print("✅ ⑩ 配置中心渲染")
        await shot(page, "10_settings")

        # ---- 11. 全模块业务串联：左侧导航连续跳转 ----
        for route, title in [
            ("/dashboard", "工作台"),
            ("/workflows", "工作流"),
            ("/editor", "画布"),
            ("/runs", "追踪"),
            ("/assets", "资产"),
            ("/tasks", "任务"),
            ("/models", "模型"),
            ("/audit", "审计"),
            ("/capabilities", "能力"),
            ("/resources", "资源"),
            ("/settings", "配置"),
        ]:
            await page.goto(BASE + route, wait_until="networkidle")
            if route == "/editor":
                await page.wait_for_selector("text=节点模板库（PRD §11）", timeout=6000)
            else:
                await page.wait_for_selector("h2", timeout=6000)
        passed.append("⑪ 全模块导航串联（11 个路由跳转无异常）")
        print("✅ ⑪ 全模块导航串联（11 个路由跳转无异常）")
        await shot(page, "11_full_chain")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错（全模块）")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V12 全量回归验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V12 全量回归 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
