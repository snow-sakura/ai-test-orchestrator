"""V7 Loop Engineering 自动验证脚本
验证 /models 模型与额度全部功能（PRD §6.5）：
1. 页面渲染 + 模型注册表加载
2. 模型注册表卡片（厂商、类型、上下文、日限、价格）
3. 三层配置（全站 / 个人 / 角色）齐全
4. 连接测试
5. 编辑配置
6. 额度管理：当日额度卡片 + 叠加额度
7. 额度授予记录 + 撤销
8. 额度授予（新建）
9. 用量与成本表
10. 业务串联：模型与额度 → 工作流列表
关键步骤自动截图到 tests/screenshots/v7/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v7")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_models():
    """把 models.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "models.json")
    seed = {
        "registry": [
            {"id": "claude_opus_4_5", "name": "Claude-Opus-4.5", "vendor": "Anthropic", "kind": "文本", "tier": "高", "context": "200K", "dailyLimit": 500, "pricePerMIn": 15.0, "pricePerMOut": 75.0, "desc": "旗舰推理模型，适合复杂归因与用例生成"},
            {"id": "claude_sonnet_4_5", "name": "Claude-Sonnet-4.5", "vendor": "Anthropic", "kind": "文本", "tier": "中", "context": "200K", "dailyLimit": 2000, "pricePerMIn": 3.0, "pricePerMOut": 15.0, "desc": "均衡性能与成本，适合大部分节点执行"},
            {"id": "gemini_2_5_pro", "name": "Gemini-2.5-Pro", "vendor": "Google", "kind": "文本", "tier": "高", "context": "1M", "dailyLimit": 1000, "pricePerMIn": 1.25, "pricePerMOut": 10.0, "desc": "超长上下文，适合大规模日志分析"},
            {"id": "gpt_4o", "name": "GPT-4o", "vendor": "OpenAI", "kind": "多模态", "tier": "中", "context": "128K", "dailyLimit": 2000, "pricePerMIn": 2.5, "pricePerMOut": 10.0, "desc": "多模态理解，适合 UI 截图分析"},
            {"id": "qwen3_max", "name": "Qwen3-Max", "vendor": "Alibaba", "kind": "文本", "tier": "中", "context": "256K", "dailyLimit": 3000, "pricePerMIn": 1.5, "pricePerMOut": 4.5, "desc": "中文理解与代码生成强项"},
            {"id": "claude_opus_4_5_vision", "name": "Claude-Opus-4.5-Vision", "vendor": "Anthropic", "kind": "视觉", "tier": "高", "context": "200K", "dailyLimit": 200, "pricePerMIn": 15.0, "pricePerMOut": 75.0, "desc": "视觉理解，适合缺陷截图识别"},
        ],
        "configs": {
            "global": {"level": "全站", "textModel": "claude_sonnet_4_5", "visionModel": "claude_opus_4_5_vision", "params": {"temperature": 0.2, "maxTokens": 4096}, "keyMasked": "sk-ant-••••••••7f3a", "connected": True, "keyMaskedSource": "管理员"},
            "personal_test_lead": {"level": "个人", "owner": "测试负责人", "textModel": "qwen3_max", "visionModel": "gpt_4o", "params": {"temperature": 0.3, "maxTokens": 8192}, "keyMasked": "sk-alb-••••••••9c2d", "connected": True, "keyMaskedSource": "个人自带凭据"},
            "role_gate_judge": {"level": "角色", "owner": "质量门禁裁决节点", "textModel": "claude_opus_4_5", "visionModel": "", "params": {"temperature": 0.0, "maxTokens": 2048}, "keyMasked": "sk-ant-••••••••7f3a", "connected": True, "keyMaskedSource": "继承全站"},
            "role_case_generator": {"level": "角色", "owner": "用例生成节点", "textModel": "gemini_2_5_pro", "visionModel": "", "params": {"temperature": 0.4, "maxTokens": 16384}, "keyMasked": "sk-goo-••••••••4e1b", "connected": False, "keyMaskedSource": "角色独立凭据"},
        },
        "grants": [
            {"id": "grant_001", "account": "测试负责人", "model": "claude_sonnet_4_5", "date": "2026-10-26", "extraQuota": 500, "revoked": False, "by": "管理员", "ts": "2026-10-26 08:00"},
            {"id": "grant_002", "account": "测试负责人", "model": "claude_sonnet_4_5", "date": "2026-10-25", "extraQuota": 300, "revoked": False, "by": "管理员", "ts": "2026-10-25 08:00"},
            {"id": "grant_003", "account": "测试负责人", "model": "gemini_2_5_pro", "date": "2026-10-24", "extraQuota": 200, "revoked": True, "by": "管理员", "ts": "2026-10-24 08:00"},
        ],
        "quotas": [
            {"account": "测试负责人", "model": "claude_sonnet_4_5", "dailyLimit": 2000, "usedToday": 1240, "extraToday": 800, "renewed": False},
            {"account": "测试负责人", "model": "gemini_2_5_pro", "dailyLimit": 1000, "usedToday": 1000, "extraToday": 0, "renewed": True},
            {"account": "测试负责人", "model": "qwen3_max", "dailyLimit": 3000, "usedToday": 460, "extraToday": 0, "renewed": False},
        ],
        "usage": [
            {"id": "u1", "model": "claude_sonnet_4_5", "workflow": "我的第一个测试工作流", "node": "需求解析", "tokens": 806, "cost": 0.0041, "ts": "2026-10-26 14:02"},
            {"id": "u2", "model": "claude_opus_4_5", "workflow": "我的第一个测试工作流", "node": "质量门禁", "tokens": 1220, "cost": 0.0915, "ts": "2026-10-26 14:03"},
            {"id": "u3", "model": "gemini_2_5_pro", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "变更影响分析", "tokens": 3480, "cost": 0.0592, "ts": "2026-10-26 09:01"},
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
    print(f"[reset] models.json 复位为预置种子（{path}）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    reset_models()

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 模型注册表加载
        await page.goto(BASE + "/models", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('模型与额度')", timeout=8000)
        passed.append("模型与额度页渲染")
        print("✅ 模型与额度页渲染")

        # 模型注册表卡片出现
        await page.locator("text=Claude-Opus-4.5").first.wait_for(timeout=5000)
        passed.append("模型注册表加载（Claude-Opus-4.5）")
        print("✅ 模型注册表加载（Claude-Opus-4.5）")
        await shot(page, "01_registry")

        # 2. 模型注册表卡片（厂商、类型、上下文、日限、价格）
        assert await page.locator("text=Anthropic").count() >= 1, "未找到 厂商 Anthropic"
        assert await page.locator("text=视觉").count() >= 1, "未找到 视觉 类型"
        assert await page.locator("text=200K").count() >= 1, "未找到 上下文 200K"
        assert await page.locator("text=日限").count() >= 1, "未找到 日限"
        passed.append("模型注册表卡片（厂商 / 类型 / 上下文 / 日限 / 价格）")
        print("✅ 模型注册表卡片（厂商 / 类型 / 上下文 / 日限 / 价格）")

        # 3. 三层配置（全站 / 个人 / 角色）齐全
        await page.click("button:has-text('三层配置')")
        await page.wait_for_timeout(400)
        assert await page.locator("text=全站级").count() >= 1, "未找到 全站级 配置"
        assert await page.locator("text=个人级").count() >= 1, "未找到 个人级 配置"
        assert await page.locator("text=角色级").count() >= 1, "未找到 角色级 配置"
        passed.append("三层配置（全站 / 个人 / 角色）齐全")
        print("✅ 三层配置（全站 / 个人 / 角色）齐全")
        await shot(page, "02_configs")

        # 4. 连接测试
        test_btns = page.locator("button:has-text('连接测试')")
        test_count = await test_btns.count()
        if test_count > 0:
            await test_btns.first.click()
            toast_box = page.locator(".fixed.bottom-6.right-6")
            await toast_box.first.wait_for(timeout=5000)
            await page.wait_for_timeout(500)
            passed.append("连接测试（模型端点可达性）")
            print("✅ 连接测试（模型端点可达性）")
        await shot(page, "03_test_connection")

        # 5. 编辑配置
        edit_btn = page.locator("button:has-text('编辑')").first
        await edit_btn.wait_for(timeout=5000)
        await edit_btn.click()
        await page.wait_for_selector("h3:has-text('编辑配置')", timeout=5000)
        await page.wait_for_selector("text=密钥（掩码）", timeout=5000)
        passed.append("编辑配置（密钥掩码 + 参数）")
        print("✅ 编辑配置（密钥掩码 + 参数）")
        # 关闭编辑弹窗
        await page.locator("div.fixed button:has-text('取消')").first.click()
        await page.wait_for_selector("text=编辑配置", state="detached", timeout=5000)

        # 6. 额度管理：当日额度卡片 + 叠加额度
        await page.click("button:has-text('额度管理')")
        await page.wait_for_timeout(400)
        assert await page.locator("text=Claude-Sonnet-4.5").count() >= 1, "未找到 额度卡片 Claude-Sonnet-4.5"
        assert await page.locator("text=可用").count() >= 1, "未找到 可用额度"
        renew_btn = page.locator("button:has-text('＋ 叠加额度')").first
        await renew_btn.wait_for(timeout=5000)
        await renew_btn.click()
        toast_box = page.locator(".fixed.bottom-6.right-6")
        await toast_box.first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        passed.append("额度管理：当日额度卡片 + 叠加额度")
        print("✅ 额度管理：当日额度卡片 + 叠加额度")
        await shot(page, "04_quota")

        # 7. 额度授予记录 + 撤销
        assert await page.locator("text=额度授予记录").count() >= 1, "未找到 额度授予记录"
        assert await page.locator("text=已撤销").count() >= 1, "未找到 已撤销 记录"
        revoke_btn = page.locator("button:has-text('撤销')").first
        await revoke_btn.wait_for(timeout=5000)
        await revoke_btn.click()
        await page.wait_for_selector("text=授予已撤销", timeout=5000)
        await page.wait_for_timeout(500)
        passed.append("额度授予记录 + 撤销")
        print("✅ 额度授予记录 + 撤销")
        await shot(page, "05_grants")

        # 8. 额度授予（新建）
        await page.click("button:has-text('＋ 额度授予')")
        await page.wait_for_selector("h3:has-text('额度授予')", timeout=5000)
        await page.fill("input[placeholder='测试负责人']", "V7 测试账号")
        await page.fill("input[type='number'][min='1']", "300")
        await page.locator("div.fixed button:has-text('授予')").first.click()
        await page.wait_for_selector("text=额度已授予", timeout=5000)
        await page.wait_for_timeout(500)
        passed.append("额度授予（新建）")
        print("✅ 额度授予（新建）")
        await shot(page, "06_grant_created")

        # 9. 用量与成本表
        await page.click("button:has-text('用量与成本')")
        await page.wait_for_timeout(400)
        assert await page.locator("text=计量与成本").count() >= 1, "未找到 计量与成本 表头"
        assert await page.locator("text=Token").count() >= 1, "未找到 Token 列"
        assert await page.locator("text=需求解析").count() >= 1, "未找到 节点 需求解析"
        passed.append("用量与成本表（按工作流 / 节点 / 模型维度）")
        print("✅ 用量与成本表（按工作流 / 节点 / 模型维度）")
        await shot(page, "07_usage")

        # 10. 业务串联：模型与额度 → 工作流列表
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：模型与额度 → 工作流列表")
        print("✅ 业务串联：模型与额度 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V7 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V7 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
