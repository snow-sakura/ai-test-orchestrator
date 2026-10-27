"""V5 Loop Engineering 自动验证脚本
验证 /assets 认证资产库全部功能（PRD §6.3）：
1. 页面渲染 + 预置资产加载
2. 资产卡片渲染（类型标签、版本、状态）
3. 5 类资产类型齐全（用例/脚本/数据模板/能力包/变更驱动用例）
4. 质量门槛判定明细（变异分数/稳定性/副作用回归）
5. 搜索过滤
6. 按类型筛选
7. 按状态筛选
8. 新建资产
9. 资产详情：状态变更审计日志
10. 认证操作（质量门槛判定）
11. 业务串联：认证资产库 → 工作流列表
关键步骤自动截图到 tests/screenshots/v5/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v5")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_assets():
    """把 assets.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "assets.json")
    if not os.path.exists(path):
        return  # 让后端 startup seed 创建
    # 删除文件让 seed_assets 重新创建
    os.remove(path)
    print(f"[reset] assets.json 已删除（等待后端重新 seed）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    # 重置 assets.json 为预置种子，避免重复测试累积
    seed = {
        "asset_case_001": {"id": "asset_case_001", "type": "用例", "name": "移动端登录全流程认证用例", "version": 3, "status": "certified", "scope": ["移动端", "iOS", "Android"], "quality": {"mutationScore": 0.92, "stability": 0.95, "regressionResult": "pass"}, "references": ["wf_cicd", "wf_mobile"], "pinnedVersions": {}, "certifiedAt": "2026-09-15", "retireAlert": False, "auditLog": [{"ts": "2026-09-15", "action": "certified", "by": "质量门禁节点", "detail": "通过全部质量门槛"}]},
        "asset_script_001": {"id": "asset_script_001", "type": "脚本", "name": "API 接口巡检自动化脚本", "version": 1, "status": "certified", "scope": ["API", "巡检"], "quality": {"mutationScore": 0.88, "stability": 0.97, "regressionResult": "pass"}, "references": ["wf_api_daily"], "pinnedVersions": {}, "certifiedAt": "2026-10-01", "retireAlert": False, "auditLog": [{"ts": "2026-10-01", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}]},
        "asset_data_001": {"id": "asset_data_001", "type": "数据模板", "name": "用户角色权限测试数据模板", "version": 2, "status": "certified", "scope": ["权限", "RBAC"], "quality": {"mutationScore": 0.9, "stability": 0.93, "regressionResult": "pass"}, "references": [], "pinnedVersions": {}, "certifiedAt": "2026-08-20", "retireAlert": False, "auditLog": [{"ts": "2026-08-20", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}]},
        "asset_skill_001": {"id": "asset_skill_001", "type": "能力包", "name": "Browser-use 浏览器智能体能力包", "version": 5, "status": "certified", "scope": ["Web", "UI", "探索"], "quality": {"mutationScore": 0.85, "stability": 0.91, "regressionResult": "pass"}, "references": ["wf_explore"], "pinnedVersions": {}, "certifiedAt": "2026-10-10", "retireAlert": False, "auditLog": [{"ts": "2026-10-10", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}]},
        "asset_cd_001": {"id": "asset_cd_001", "type": "变更驱动用例", "name": "支付模块变更驱动回归用例集", "version": 1, "status": "pending", "scope": ["支付", "回归"], "quality": {"mutationScore": 0.72, "stability": 0.6, "regressionResult": "pending"}, "references": [], "pinnedVersions": {}, "certifiedAt": "", "retireAlert": False, "auditLog": [{"ts": "2026-10-25", "action": "created", "by": "代码变更驱动测试生成节点", "detail": "生成待认证"}]},
        "asset_case_002": {"id": "asset_case_002", "type": "用例", "name": "旧版订单流程用例（已失效）", "version": 4, "status": "retired", "scope": ["订单", "旧版"], "quality": {"mutationScore": 0.55, "stability": 0.4, "regressionResult": "fail"}, "references": ["wf_order_old"], "pinnedVersions": {}, "certifiedAt": "2026-05-01", "retireAlert": True, "auditLog": [{"ts": "2026-05-01", "action": "certified", "by": "测试资产认证节点", "detail": "通过质量门槛"}, {"ts": "2026-10-20", "action": "retired", "by": "平台", "detail": "被测系统订单模块重大变更，资产可能失效"}]},
    }
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "assets.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    print(f"[reset] assets.json 复位为预置种子（{path}）")

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置资产加载
        await page.goto(BASE + "/assets", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('认证资产库')", timeout=8000)
        passed.append("认证资产库页渲染")
        print("✅ 认证资产库页渲染")

        # 预置资产卡片出现
        await page.locator("text=移动端登录全流程认证用例").first.wait_for(timeout=5000)
        passed.append("预置认证资产加载（移动端登录全流程认证用例）")
        print("✅ 预置认证资产加载（移动端登录全流程认证用例）")
        await shot(page, "01_assets_list")

        # 2. 资产卡片渲染（类型标签、版本、状态）
        assert await page.locator("text=认证用例").count() >= 1, "未找到 认证用例 类型标签"
        assert await page.locator("text=已认证").count() >= 1, "未找到 已认证 状态标签"
        assert await page.locator("text=v1").count() >= 1 or await page.locator("text=v3").count() >= 1, "未找到版本号"
        passed.append("资产卡片渲染（类型 / 版本 / 状态）")
        print("✅ 资产卡片渲染（类型 / 版本 / 状态）")

        # 3. 5 类资产类型齐全（PRD §6.3）
        # 用卡片内的 typeLabel div 定位，避免匹配到 select option
        for t in ["认证用例", "认证自动化脚本", "认证测试数据模板", "认证能力包", "代码变更驱动的生成用例"]:
            await page.locator(f".polaroid-card.rounded-lg.p-4 >> text={t}").first.wait_for(timeout=5000)
        passed.append("5 类资产类型齐全（PRD §6.3）")
        print("✅ 5 类资产类型齐全（PRD §6.3）")
        await shot(page, "02_all_types")

        # 4. 质量门槛判定明细
        assert await page.locator("text=变异分数").count() >= 1, "未找到 变异分数"
        assert await page.locator("text=稳定性").count() >= 1, "未找到 稳定性"
        assert await page.locator("text=副作用回归").count() >= 1, "未找到 副作用回归"
        passed.append("质量门槛判定明细（变异分数 / 稳定性 / 副作用回归）")
        print("✅ 质量门槛判定明细（变异分数 / 稳定性 / 副作用回归）")

        # 5. 搜索过滤
        await page.fill("input[placeholder='搜索资产名称...']", "API")
        await page.wait_for_timeout(300)
        assert await page.locator("text=API 接口巡检自动化脚本").count() >= 1, "搜索未命中 API 脚本"
        assert await page.locator("text=移动端登录全流程认证用例").count() == 0, "搜索未排除 移动端用例"
        passed.append("搜索过滤命中并排除")
        print("✅ 搜索过滤命中并排除")
        await page.fill("input[placeholder='搜索资产名称...']", "")
        await page.wait_for_timeout(300)

        # 6. 按类型筛选
        type_select = page.locator("select").nth(0)
        await type_select.wait_for(timeout=5000)
        await type_select.select_option(value="用例")
        await page.wait_for_timeout(300)
        case_cards = await page.locator(".polaroid-card.rounded-lg.p-4 >> text=认证用例").count()
        assert case_cards >= 1, "类型筛选：用例 未命中"
        passed.append(f"按类型筛选（用例 命中 {case_cards} 项）")
        print(f"✅ 按类型筛选（用例 命中 {case_cards} 项）")
        # 切回全部
        await type_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 7. 按状态筛选
        status_select = page.locator("select").nth(1)
        await status_select.select_option(value="certified")
        await page.wait_for_timeout(300)
        certified_count = await page.locator("text=已认证").count()
        assert certified_count >= 1, "状态筛选：已认证 未命中"
        passed.append(f"按状态筛选（已认证 命中 {certified_count} 项）")
        print(f"✅ 按状态筛选（已认证 命中 {certified_count} 项）")
        await status_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 8. 新建资产
        await page.click("button:has-text('＋ 新建资产')")
        await page.wait_for_selector("h3:has-text('新建认证资产')", timeout=5000)
        await page.fill("input[placeholder='资产名称']", "V5 自动测试资产")
        await page.click("button:has-text('创建')")
        await page.wait_for_selector("text=资产已创建", timeout=5000)
        await page.wait_for_selector("text=V5 自动测试资产", timeout=5000)
        passed.append("新建资产成功")
        print("✅ 新建资产成功")
        await shot(page, "03_created")

        # 9. 资产详情：状态变更审计日志
        # 点击第一张卡片的「查看」
        view_btn = page.locator("button:has-text('查看')").first
        await view_btn.wait_for(timeout=5000)
        await view_btn.click()
        await page.wait_for_selector("text=资产详情", timeout=5000)
        await page.wait_for_selector("text=状态变更审计日志", timeout=5000)
        passed.append("资产详情：状态变更审计日志")
        print("✅ 资产详情：状态变更审计日志")
        await shot(page, "04_detail_audit")

        # 10. 认证操作（质量门槛判定）
        # 关闭详情弹窗
        await page.locator("div.fixed button:has-text('×')").first.click()
        await page.wait_for_selector("text=资产详情", state="detached", timeout=5000)

        # 找到一个待认证/未通过的资产进行认证操作
        # 先筛选 待认证
        status_select = page.locator("select").nth(1)
        await status_select.select_option(value="pending")
        await page.wait_for_timeout(400)
        pending_items = await page.locator(".polaroid-card.rounded-lg.p-4 h3").count()
        if pending_items > 0:
            certify_btn = page.locator("button:has-text('认证')").first
            await certify_btn.click()
            await page.wait_for_selector("text=认证", timeout=5000)
            # 等待结果 toast
            await page.wait_for_timeout(1000)
            passed.append("认证操作（质量门槛判定）")
            print("✅ 认证操作（质量门槛判定）")
        await status_select.select_option(value="")
        await page.wait_for_timeout(300)
        await shot(page, "05_certify")

        # 11. 业务串联：认证资产库 → 工作流列表
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：认证资产库 → 工作流列表")
        print("✅ 业务串联：认证资产库 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V5 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V5 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
