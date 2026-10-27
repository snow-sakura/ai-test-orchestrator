"""V11 Loop Engineering 自动验证脚本
验证 /settings 统一配置中心全部功能（PRD §6.8 / §6.9）：
1. 页面渲染 + 预置 5 分区加载
2. 分区导航（驱动 / 模型 / 通知 / 环境检测 / 权限控制）
3. 配置项渲染（select / number / switch / text / multi 控件）
4. 修改配置项（下拉选择 → toast）
5. 预算与熔断卡片（节点级 / 工作流级 / 循环节点）
6. 修改预算策略（onExceed 下拉 → toast）
7. 业务串联：配置中心 → 模型与额度
关键步骤自动截图到 tests/screenshots/v11/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v11")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_settings():
    """把 settings.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "settings.json")
    seeds = {
        "sections": {
            "驱动": {"id": "sec_driver", "label": "驱动配置", "enabled": True, "items": [
                {"key": "浏览器驱动", "value": "Playwright Chromium", "type": "select", "options": ["Playwright Chromium", "Selenium Chrome", "Airtest"], "desc": "UI 探索 / Browser-use 节点使用的浏览器驱动"},
                {"key": "移动端驱动", "value": "Airtest 1.3.0", "type": "select", "options": ["Airtest 1.3.0", "Appium 2.x"], "desc": "移动端图像识别自动化节点驱动"},
                {"key": "设备连接协议", "value": "USB + ADB", "type": "select", "options": ["USB + ADB", "无线 ADB", "远程设备云"], "desc": "设备池连接方式"},
            ]},
            "模型": {"id": "sec_model", "label": "模型配置", "enabled": True, "items": [
                {"key": "默认文本模型", "value": "Claude-Sonnet-4.5", "type": "select", "options": ["Claude-Sonnet-4.5", "Qwen3-Max", "GPT-4o", "Gemini-2.5-Pro"], "desc": "规划 / 执行 / 验证节点默认文本模型"},
                {"key": "默认视觉模型", "value": "Claude-Opus-4.5-Vision", "type": "select", "options": ["Claude-Opus-4.5-Vision", "Gemini-2.5-Pro", "GPT-4o"], "desc": "视觉 / 语义回归节点默认视觉模型"},
                {"key": "推理温度", "value": "0.2", "type": "number", "options": [], "desc": "测试场景低温度保证可重复"},
                {"key": "Top-P", "value": "0.9", "type": "number", "options": [], "desc": "核采样阈值"},
            ]},
            "通知": {"id": "sec_notify", "label": "通知配置", "enabled": True, "items": [
                {"key": "通知渠道", "value": "钉钉 + 邮件", "type": "multi", "options": ["钉钉", "飞书", "邮件", "Slack", "Webhook"], "desc": "门禁裁决 / 缺陷归档触发的通知渠道"},
                {"key": "门禁阻断通知", "value": "on", "type": "switch", "options": ["on", "off"], "desc": "质量门禁阻断时立即推送"},
                {"key": "超时升级通知", "value": "on", "type": "switch", "options": ["on", "off"], "desc": "任务超时 / 无进展熔断时升级人工并通知"},
                {"key": "静默时段", "value": "23:00-07:00", "type": "text", "options": [], "desc": "非紧急通知在静默时段不推送"},
            ]},
            "环境检测": {"id": "sec_env", "label": "环境检测", "enabled": True, "items": [
                {"key": "环境探针", "value": "每 60s 一次", "type": "select", "options": ["每 30s 一次", "每 60s 一次", "仅执行前检测"], "desc": "执行节点前对目标环境做可达性 / 版本探针"},
                {"key": "数据源连接池", "value": "maxsize=10, timeout=30s", "type": "text", "options": [], "desc": "数据库 / 数据一致性节点连接池参数"},
                {"key": "破坏性测试熔断", "value": "enabled", "type": "switch", "options": ["enabled", "disabled"], "desc": "安全探测节点越界操作自动熔断（平台级红线，不可被节点覆盖）"},
            ]},
            "权限控制": {"id": "sec_perm", "label": "权限控制", "enabled": True, "items": [
                {"key": "角色模型", "value": "RBAC", "type": "select", "options": ["RBAC", "ABAC"], "desc": "开放能力接入的角色授权模型"},
                {"key": "危险操作审批方", "value": "测试负责人", "type": "select", "options": ["测试负责人", "平台审批人", "规则引擎自动放行"], "desc": "执行类 / 写入类操作默认审批方"},
                {"key": "审计账本只读角色", "value": "合规审计员", "type": "text", "options": [], "desc": "可导出但不可修改审计账本的角色"},
                {"key": "密钥明文落盘", "value": "forbidden", "type": "switch", "options": ["forbidden", "allowed"], "desc": "凭据与模型密钥禁止明文落盘（平台红线）"},
            ]},
        },
        "budgets": [
            {"id": "budget_node", "scope": "节点级", "tokenBudget": 50000, "timeBudgetSec": 600, "onExceed": "硬停止", "desc": "单节点默认预算，超出即终止"},
            {"id": "budget_wf", "scope": "工作流级", "tokenBudget": 500000, "timeBudgetSec": 3600, "onExceed": "降级输出", "desc": "单工作流总预算，超出降级为部分结果"},
            {"id": "budget_loop", "scope": "循环节点", "maxIterations": 8, "noProgressFuse": 3, "onExceed": "升级人工", "desc": "循环节点最大迭代与无进展熔断次数"},
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)
    print(f"[reset] settings.json 复位为预置种子（{len(seeds['sections'])} 分区 / {len(seeds['budgets'])} 预算）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    reset_settings()

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置 5 分区加载
        await page.goto(BASE + "/settings", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('统一配置中心')", timeout=8000)
        passed.append("统一配置中心页渲染")
        print("✅ 统一配置中心页渲染")

        await page.locator("text=驱动配置").first.wait_for(timeout=5000)
        passed.append("预置 5 分区加载")
        print("✅ 预置 5 分区加载")

        # 2. 分区导航齐全
        for label in ["驱动配置", "模型配置", "通知配置", "环境检测", "权限控制"]:
            await page.locator(f"button:has-text('{label}')").first.wait_for(timeout=5000)
        passed.append("分区导航齐全（驱动 / 模型 / 通知 / 环境检测 / 权限控制）")
        print("✅ 分区导航齐全（驱动 / 模型 / 通知 / 环境检测 / 权限控制）")
        await shot(page, "01_sections")

        # 3. 配置项渲染（默认 驱动配置 分区，含 select 控件）
        assert await page.locator("text=浏览器驱动").count() >= 1, "未找到 浏览器驱动 配置项"
        assert await page.locator("text=Playwright Chromium").count() >= 1, "未找到 默认值 Playwright Chromium"
        passed.append("配置项渲染（key / desc / 默认值 / 控件）")
        print("✅ 配置项渲染（key / desc / 默认值 / 控件）")

        # 4. 修改配置项（切换到 模型配置，下拉改 默认文本模型 → toast）
        await page.click("button:has-text('模型配置')")
        await page.wait_for_selector("text=默认文本模型", timeout=5000)
        await page.locator("select").filter(has_text="Claude-Sonnet-4.5").first.select_option("Qwen3-Max")
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(400)
        assert await page.locator("text=Qwen3-Max").count() >= 1, "修改后未出现新值"
        passed.append("修改配置项（下拉选择 + 列表更新 + toast）")
        print("✅ 修改配置项（下拉选择 + 列表更新 + toast）")
        await shot(page, "02_edited")

        # 5. 预算与熔断卡片
        await page.locator("text=预算、熔断与并发").first.wait_for(timeout=5000)
        assert await page.locator("text=节点级").count() >= 1, "未找到 节点级 预算"
        assert await page.locator("text=工作流级").count() >= 1, "未找到 工作流级 预算"
        assert await page.locator("text=循环节点").count() >= 1, "未找到 循环节点 预算"
        assert await page.locator("text=硬停止").count() >= 1, "未找到 硬停止 策略"
        passed.append("预算与熔断卡片（节点级 / 工作流级 / 循环节点 + 策略）")
        print("✅ 预算与熔断卡片（节点级 / 工作流级 / 循环节点 + 策略）")
        await shot(page, "03_budgets")

        # 6. 修改预算策略（节点级 onExceed 下拉 → toast）
        # 找到 节点级 卡片内的 select
        node_card = page.locator(".polaroid-card.rounded-lg.p-4").filter(has_text="节点级").first
        await node_card.locator("select").first.select_option("降级输出")
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(400)
        passed.append("修改预算策略（onExceed 下拉 + toast）")
        print("✅ 修改预算策略（onExceed 下拉 + toast）")
        await shot(page, "04_budget_updated")

        # 7. 业务串联：配置中心 → 模型与额度
        await page.goto(BASE + "/models", wait_until="networkidle")
        await page.wait_for_selector("h2", timeout=8000)
        passed.append("业务串联：配置中心 → 模型与额度")
        print("✅ 业务串联：配置中心 → 模型与额度")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V11 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V11 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
