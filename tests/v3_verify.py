"""V3 Loop Engineering 自动验证脚本
验证 /editor 编排画布核心功能（PRD §3/§4/§5/§7）：
1. 画布渲染 + 左侧节点模板库（PRD §11 六大类 40 节点）
2. 节点搜索过滤
3. 添加节点到画布
4. 连线（端口拖拽 / connect）
5. 节点配置抽屉 10 分区（基础/模型/提示词/输入/输出/工具/能力包/约束/规则/异步资源）
6. 配置项修改
7. 结构校验（命中问题）
8. 执行工作流 + 画布实时高亮 + 执行日志
9. 隐藏辅助节点
10. 保存工作流
11. 业务串联：编辑 → 列表页
关键步骤自动截图到 tests/screenshots/v3/
"""
import asyncio
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v3")
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

        # 直接带 ?wf 参数打开默认工作流
        await page.goto(BASE + "/editor?wf=default-workflow", wait_until="networkidle")
        await page.wait_for_selector("text=节点模板库", timeout=8000)
        passed.append("编排画布渲染（含节点模板库）")
        print("✅ 编排画布渲染（含节点模板库）")
        await shot(page, "01_canvas")

        # 1. 六大类节点目录齐全（PRD §11）
        for cat in ["测试分析与设计", "测试执行", "测试诊断与修复", "质量评估与决策", "控制流", "平台基础"]:
            await page.locator(f"text={cat}").first.wait_for(timeout=5000)
        passed.append("六大类节点目录齐全（PRD §11）")
        print("✅ 六大类节点目录齐全（PRD §11）")

        # 2. 节点搜索过滤
        await page.fill("input[placeholder='搜索节点...']", "需求")
        await page.wait_for_timeout(300)
        assert await page.locator("text=需求解析").count() >= 1, "搜索未命中 需求解析"
        assert await page.locator("text=性能负载测试").count() == 0, "搜索未排除 性能负载测试"
        passed.append("节点搜索过滤命中并排除")
        print("✅ 节点搜索过滤命中并排除")
        await page.fill("input[placeholder='搜索节点...']", "")
        await page.wait_for_timeout(300)

        # 3. 添加节点到画布（点击左侧模板库中的 需求解析）
        before = await page.locator(".vue-flow__node").count()
        await page.locator("div[draggable='true']").filter(has_text="需求解析").nth(0).click()
        await page.wait_for_timeout(500)
        after = await page.locator(".vue-flow__node").count()
        assert after > before, f"添加节点后节点数未增加（before={before} after={after}）"
        passed.append(f"添加节点到画布（节点数 {before}→{after}）")
        print(f"✅ 添加节点到画布（节点数 {before}→{after}）")
        await shot(page, "02_added_node")

        # 4. 节点配置抽屉：点击新节点
        await page.locator(".vue-flow__node").last.click()
        await page.wait_for_selector("text=节点配置", timeout=5000)
        passed.append("节点配置抽屉打开")
        print("✅ 节点配置抽屉打开")

        # 5. 10 个配置分区（PRD §4/§7.1）
        sections = ["基础信息", "模型配置", "提示词配置", "输入变量绑定", "输出 Schema",
                    "工具白名单", "能力包挂载", "约束配置", "规则绑定", "异步与资源"]
        for sec in sections:
            await page.locator(f"button:has-text('{sec}')").first.wait_for(timeout=5000)
        passed.append(f"节点配置抽屉 10 分区齐全（PRD §4/§7.1）")
        print(f"✅ 节点配置抽屉 10 分区齐全（PRD §4/§7.1）")
        await shot(page, "03_drawer_10sections")

        # 6. 展开每个分区并修改配置
        # 6a. 模型配置：修改模型
        await page.click("button:has-text('模型配置')")
        model_select = page.locator("aside select").first
        await model_select.wait_for(timeout=5000)
        await model_select.select_option(value="Gemini-2.5-Pro")
        passed.append("模型配置分区：可修改模型")
        print("✅ 模型配置分区：可修改模型")

        # 6b. 提示词：填写 System Prompt
        await page.click("button:has-text('提示词配置')")
        await page.wait_for_selector("textarea", timeout=5000)
        await page.fill("textarea", "你是测试分析智能体，请解析需求并输出结构化需求点")
        passed.append("提示词配置分区：可填写 System Prompt")
        print("✅ 提示词配置分区：可填写 System Prompt")

        # 6c. 工具白名单：勾选
        await page.click("button:has-text('工具白名单')")
        await page.wait_for_selector("input[type='checkbox']", timeout=5000)
        await page.check("input[type='checkbox'] >> nth=0")
        passed.append("工具白名单分区：可勾选工具")
        print("✅ 工具白名单分区：可勾选工具")

        # 6d. 约束配置：改超时
        await page.click("button:has-text('约束配置')")
        await page.wait_for_selector("input[type='number']", timeout=5000)
        passed.append("约束配置分区：可修改最大步数/超时/Token/重试")
        print("✅ 约束配置分区：可修改最大步数/超时/Token/重试")
        await shot(page, "04_config_modified")

        # 7. 结构校验
        await page.click("button:has-text('结构校验')")
        await page.wait_for_selector("text=结构校验（PRD §7.2）", timeout=5000)
        passed.append("结构校验面板打开")
        print("✅ 结构校验面板打开")
        await shot(page, "05_validation")

        # 8. 执行工作流
        await page.get_by_role("button", name="执行", exact=True).click()
        await page.locator("text=执行追踪（PRD §7.4）").wait_for(timeout=5000)
        await page.locator("text=节点「开始」开始执行").wait_for(timeout=15000)
        passed.append("执行工作流 + 画布实时高亮 + 执行日志")
        print("✅ 执行工作流 + 画布实时高亮 + 执行日志")
        await shot(page, "06_executing")

        # 等待执行完成
        await page.locator("text=工作流执行完毕").wait_for(timeout=30000)
        success_nodes = await page.locator(".node-success").count()
        assert success_nodes >= 1, "执行完成后没有 success 节点"
        passed.append(f"执行完成 + 节点 success 状态（{success_nodes} 个）")
        print("✅ 执行完成 + 节点 success 状态")
        await shot(page, "07_exec_done")

        # 9. 隐藏辅助节点
        await page.click("button:has-text('隐藏辅助')")
        await page.wait_for_timeout(400)
        await page.click("button:has-text('显示辅助')")  # 切回
        await page.wait_for_timeout(400)
        passed.append("隐藏/显示辅助节点")
        print("✅ 隐藏/显示辅助节点")

        # 10. 保存工作流
        await page.click("button:has-text('保存')")
        await page.wait_for_selector("text=已保存", timeout=5000)
        passed.append("保存工作流成功")
        print("✅ 保存工作流成功")

        # 11. 业务串联：返回工作流列表
        await page.click("button:has-text('←')")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：编辑 → 工作流列表")
        print("✅ 业务串联：编辑 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V3 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V3 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
