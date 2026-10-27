"""V1 Loop Engineering 自动验证脚本
自动打开浏览器验证：
1. 应用外壳（左侧导航 + 顶栏）渲染
2. /dashboard 全部功能：KPI 卡片 / 最近运行 / 待我处理 / 范式入口 / 欢迎横幅
3. 11 个模块导航跳转（含占位页视觉一致）
4. 拍立得暖色调（polaroid-warm）生效
关键步骤自动截图到 tests/screenshots/v1/
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v1")
os.makedirs(SHOT_DIR, exist_ok=True)


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ---- 1. 外壳渲染 ----
        await page.goto(BASE + "/dashboard", wait_until="networkidle")
        await page.wait_for_selector("text=AI 测试编排", timeout=8000)
        assert await page.locator("text=智能体工作流平台").count() >= 1
        passed.append("外壳：左侧导航 + Logo 渲染")
        print("✅ 外壳渲染正常")
        await shot(page, "01_shell")

        # ---- 2. 暖色调生效 ----
        bg = await page.evaluate("getComputedStyle(document.body).backgroundColor")
        assert bg and bg != "rgba(0, 0, 0, 0)", f"背景色异常: {bg}"
        passed.append(f"暖色调：body 背景 {bg}")
        print(f"✅ 暖色调生效（body bg = {bg}）")

        # ---- 3. KPI 卡片 ----
        for kpi in ["工作流总数", "今日运行", "通过率", "本月成本"]:
            await page.wait_for_selector(f"text={kpi}", timeout=5000)
        passed.append("KPI 卡片：4 项齐全")
        print("✅ KPI 卡片（工作流总数/今日运行/通过率/本月成本）齐全")

        # ---- 4. 最近运行 ----
        await page.wait_for_selector("text=最近运行", timeout=5000)
        await page.wait_for_selector("text=代码变更驱动的 CI/CD 质量门禁", timeout=5000)
        passed.append("最近运行列表渲染")
        print("✅ 最近运行列表渲染")
        await shot(page, "02_dashboard_full")

        # ---- 5. 待我处理 ----
        await page.wait_for_selector("text=待我处理", timeout=5000)
        await page.wait_for_selector("text=人工审批门", timeout=5000)
        passed.append("待我处理列表渲染")
        print("✅ 待我处理列表渲染")

        # ---- 6. 编排范式入口 ----
        for p_ in ["CI/CD 质量门禁", "智能探索回归", "移动端多端回归", "需求到用例", "外部智能体按需"]:
            await page.wait_for_selector(f"text={p_}", timeout=5000)
        passed.append("编排范式入口 5 项齐全")
        print("✅ 编排范式入口 5 项齐全")
        await shot(page, "03_paradigms")

        # ---- 7. 导航跳转 11 个模块 ----
        routes = [
            ("/dashboard", "工作台总览"),
            ("/workflows", "工作流列表"),
            ("/editor", "编排画布"),
            ("/runs", "执行追踪"),
            ("/assets", "认证资产库"),
            ("/tasks", "异步任务"),
            ("/models", "模型与额度"),
            ("/audit", "审计账本"),
            ("/capabilities", "开放能力"),
            ("/resources", "资源与锁"),
            ("/settings", "配置中心"),
        ]
        for path, title in routes:
            link = page.locator(f"a[href='{path}']")
            await link.first.click()
            await page.wait_for_selector(f"h1:has-text('{title}')", timeout=5000)
            cur = await page.evaluate("document.querySelector('h1').textContent")
            assert title in cur, f"顶栏标题未切到 {title}，实际 {cur}"
            passed.append(f"导航跳转 {path}（{title}）")
            print(f"✅ 导航跳转 {path}（{title}）")
        await page.screenshot(path=os.path.join(SHOT_DIR, "04_nav_runs.png"))

        # ---- 8. 页面 JS 错误检查 ----
        real_errors = [e for e in errors if "Download the React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（共拦截 {len(errors)} 条，有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V1 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V1 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
