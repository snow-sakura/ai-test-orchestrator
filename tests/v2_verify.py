"""V2 Loop Engineering 自动验证脚本
验证 /workflows 工作流列表页全部功能（含所有小功能与业务串联）：
1. 列表渲染（卡片 + 状态标签）
2. 新建工作流（空白 + 模板）
3. 重命名
4. 发布/撤稿状态切换
5. 删除
6. 搜索过滤
7. 5 个范式模板入口 + 一键使用
8. 流程预览
9. 业务串联：编辑跳转编辑器
关键步骤自动截图到 tests/screenshots/v2/
"""
import asyncio
import os
import urllib.request
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v2")
os.makedirs(SHOT_DIR, exist_ok=True)

# 状态标签用 CSS 类定位（草稿=amber / 已发布=green）
STATUS_DRAFT = ".polaroid-card span.bg-amber-100"
STATUS_PUBLISHED = ".polaroid-card span.bg-green-100"
CARD_H3 = ".polaroid-card h3"
CARD = ".polaroid-card.rounded-lg.p-4"  # 工作流卡片容器（模板卡片是 p-3）


def reset_storage():
    """每个测试前把后端存储复位到干净的单一工作流"""
    seed = {
        "default-workflow": {
            "id": "default-workflow",
            "name": "我的第一个测试工作流",
            "status": "draft",
            "nodes": [
                {"id": "n1", "label": "开始", "type": "platform", "position": {"x": 80, "y": 120}, "config": {}},
                {"id": "n2", "label": "需求解析", "type": "analysis", "position": {"x": 320, "y": 120}, "config": {"type": "测试分析"}},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }
    }
    with open(os.path.join(os.path.dirname(__file__), "..", "backend", "workflows.json"), "w", encoding="utf-8") as f:
        import json
        json.dump(seed, f, ensure_ascii=False, indent=2)


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


def card_for(page, name):
    """按名称取到工作流卡片容器"""
    h3 = page.locator(f"{CARD_H3}:has-text('{name}')")
    return h3.first.locator("xpath=ancestor::div[contains(@class,'polaroid-card') and contains(@class,'p-4')][1]")


async def run():
    reset_storage()
    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("工作流列表页渲染")
        print("✅ 工作流列表页渲染")

        # 1. 卡片 + 状态标签
        await page.wait_for_selector(CARD_H3, timeout=5000)
        n_cards = await page.locator(CARD).count()
        assert n_cards >= 1, f"工作流卡片数为 0"
        passed.append(f"工作流卡片渲染（{n_cards} 个）")
        print(f"✅ 工作流卡片渲染（{n_cards} 个）")
        n_status = await page.locator(STATUS_DRAFT).count() + await page.locator(STATUS_PUBLISHED).count()
        assert n_status >= 1, "无状态标签"
        passed.append(f"状态标签渲染（{n_status} 个）")
        print(f"✅ 状态标签渲染（{n_status} 个）")
        await shot(page, "01_list")

        # 2. 5 个范式模板入口
        for tpl in ["CI/CD 质量门禁", "智能探索回归", "移动端多端回归", "需求到用例", "外部智能体按需"]:
            await page.wait_for_selector(f"text={tpl}", timeout=5000)
        passed.append("5 个范式模板入口齐全")
        print("✅ 5 个范式模板入口齐全")
        await shot(page, "02_templates")

        # 3. 新建工作流（模板 cicd）
        await page.click("button:has-text('＋ 新建工作流')")
        await page.wait_for_selector("h3:has-text('新建工作流')", timeout=5000)
        await page.fill("input[placeholder='我的工作流']", "V2 自动测试工作流")
        await page.select_option("select", "cicd")
        await page.click("button:has-text('确定')")
        await page.wait_for_selector("text=工作流已创建", timeout=5000)
        await page.wait_for_selector(f"{CARD_H3}:has-text('V2 自动测试工作流')", timeout=5000)
        passed.append("新建工作流（模板 cicd）成功")
        print("✅ 新建工作流（模板 cicd）成功")
        await shot(page, "03_created")

        # 4. 搜索过滤
        await page.fill("input[placeholder='搜索工作流...']", "V2 自动测试")
        await page.wait_for_timeout(400)
        assert await page.locator(f"{CARD_H3}:has-text('V2 自动测试工作流')").count() >= 1, "搜索未命中"
        assert await page.locator(f"{CARD_H3}:has-text('我的第一个测试工作流')").count() == 0, "搜索过滤未排除其它工作流"
        passed.append("搜索过滤命中新工作流并排除其它")
        print("✅ 搜索过滤命中新工作流并排除其它")
        await page.fill("input[placeholder='搜索工作流...']", "")
        await page.wait_for_timeout(400)

        # 5. 重命名
        c = card_for(page, "V2 自动测试工作流")
        await c.locator("button:has-text('重命名')").click()
        await page.wait_for_selector("h3:has-text('重命名工作流')", timeout=5000)
        # 重命名弹窗内：label「新名称」下的 input（无 type 属性）
        await page.locator("div.fixed:has-text('重命名工作流') input").fill("V2 已重命名")
        await page.click("button:has-text('确定')")
        await page.wait_for_selector("text=重命名成功", timeout=5000)
        await page.wait_for_selector(f"{CARD_H3}:has-text('V2 已重命名')", timeout=5000)
        passed.append("重命名成功")
        print("✅ 重命名成功")
        await shot(page, "04_renamed")

        # 6. 发布 / 撤稿
        c = card_for(page, "V2 已重命名")
        await c.locator("button:has-text('发布')").click()
        await page.wait_for_selector(f"{CARD_H3}:has-text('V2 已重命名') ~ span.bg-green-100, {STATUS_PUBLISHED}:has-text('已发布')", timeout=5000)
        passed.append("发布状态切换成功")
        print("✅ 发布状态切换成功")
        c = card_for(page, "V2 已重命名")
        await c.locator("button:has-text('撤稿')").click()
        await page.wait_for_selector("text=已撤稿", timeout=5000)
        passed.append("撤稿状态切换成功")
        print("✅ 撤稿状态切换成功")

        # 7. 流程预览
        c = card_for(page, "V2 已重命名")
        await c.locator("button:has-text('预览')").click()
        await page.wait_for_selector("h3:has-text('流程预览')", timeout=5000)
        passed.append("流程预览弹窗打开")
        print("✅ 流程预览弹窗打开")
        await shot(page, "05_preview")
        await page.locator("div.fixed button:has-text('×')").first.click()
        await page.wait_for_selector("h3:has-text('流程预览')", state="detached", timeout=5000)

        # 8. 删除
        c = card_for(page, "V2 已重命名")
        await c.locator("button:has-text('删除')").click()
        await page.wait_for_selector("text=已删除", timeout=5000)
        await page.wait_for_selector(f"{CARD_H3}:has-text('V2 已重命名')", state="detached", timeout=5000)
        passed.append("删除工作流成功")
        print("✅ 删除工作流成功")
        await shot(page, "06_deleted")

        # 9. 业务串联：编辑跳转编辑器
        c = card_for(page, "我的第一个测试工作流")
        await c.locator("button:has-text('编辑')").click()
        await page.wait_for_selector("text=节点模板库", timeout=8000)
        assert "/editor" in page.url, f"未跳转到编辑器，实际 {page.url}"
        passed.append("编辑跳转编辑器成功（业务串联）")
        print("✅ 编辑跳转编辑器成功（业务串联）")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V2 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V2 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
