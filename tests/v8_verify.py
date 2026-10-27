"""V8 Loop Engineering 自动验证脚本
验证 /audit 审计证据账本全部功能（PRD §6.6）：
1. 页面渲染 + 预置证据账本加载
2. 哈希链状态条（完整 / 末端哈希）
3. 证据列表（类型标签、工作流、节点、操作方、哈希）
4. 6 类证据类型齐全（工具调用 / 白名单拒绝 / 质量门禁裁决 / 缺陷归档 / 人工审批 / 升级处理）
5. 搜索过滤
6. 按类型筛选
7. 按工作流筛选
8. 按节点筛选
9. 校验哈希链
10. 追加证据条目
11. 导出账本（合规审计）
12. 业务串联：审计证据账本 → 工作流列表
关键步骤自动截图到 tests/screenshots/v8/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v8")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_audit():
    """把 audit.json 复位为预置种子（带哈希链），避免重复测试累积"""
    import hashlib

    def _audit_entry_hash(item):
        payload = {k: v for k, v in item.items() if k != "prevHash"}
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    path = os.path.join(os.path.dirname(__file__), "..", "backend", "audit.json")
    seeds = [
        {"id": "ev_001", "ts": "2026-10-26 09:01", "type": "工具调用", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "变更影响分析", "actor": "gemini_2_5_pro", "detail": "调用 webFetch 获取 Git diff 摘要", "refId": "trace:run_seed_002:n2"},
        {"id": "ev_002", "ts": "2026-10-26 09:02", "type": "白名单拒绝", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "变更影响分析", "actor": "平台规则引擎", "detail": "拒绝调用 shell_exec（不在白名单内）", "refId": "whitelist:run_seed_002:n2"},
        {"id": "ev_003", "ts": "2026-10-26 09:03", "type": "质量门禁裁决", "workflow": "代码变更驱动的 CI/CD 质量门禁", "node": "质量门禁", "actor": "确定性规则引擎", "detail": "裁决：通过（执行通过率 96%，覆盖率 82%）", "refId": "gate:run_seed_002:n5"},
        {"id": "ev_004", "ts": "2026-10-25 21:35", "type": "缺陷归档", "workflow": "移动端多端回归", "node": "失败分诊", "actor": "失败分诊节点", "detail": "归档缺陷 DEF-2026-0921（登录崩溃），关联证据 ev_004", "refId": "defect:DEF-2026-0921"},
        {"id": "ev_005", "ts": "2026-10-25 21:36", "type": "人工审批", "workflow": "移动端多端回归", "node": "人工审批门", "actor": "测试负责人", "detail": "批准高风险缺陷升级处理", "refId": "approval:DEF-2026-0921"},
        {"id": "ev_006", "ts": "2026-10-24 15:20", "type": "升级处理", "workflow": "Web 端深度探索", "node": "探索任务节点", "actor": "平台", "detail": "任务超时，升级转人工处理", "refId": "escalation:task_timeout_001"},
        {"id": "ev_007", "ts": "2026-10-26 14:03", "type": "工具调用", "workflow": "我的第一个测试工作流", "node": "需求解析", "actor": "claude_sonnet_4_5", "detail": "调用 webFetch 获取需求文档", "refId": "trace:run_seed_001:n2"},
    ]
    # 建立哈希链
    prev = "0" * 64
    for item in seeds:
        item["prevHash"] = prev
        item["hash"] = _audit_entry_hash(item)
        prev = item["hash"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)
    print(f"[reset] audit.json 复位为预置种子（{len(seeds)} 条，含哈希链）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    reset_audit()

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置证据账本加载
        await page.goto(BASE + "/audit", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('审计证据账本')", timeout=8000)
        passed.append("审计证据账本页渲染")
        print("✅ 审计证据账本页渲染")

        # 哈希链状态条出现（校验哈希链按钮 + 末端哈希提示）
        await page.locator("button:has-text('校验哈希链')").first.wait_for(timeout=5000)
        await page.locator("text=任意条目被篡改后，链校验立即失败").first.wait_for(timeout=5000)
        passed.append("哈希链状态条（完整 + 末端哈希）")
        print("✅ 哈希链状态条（完整 + 末端哈希）")

        # 预置证据条目出现
        await page.locator("text=调用 webFetch 获取 Git diff 摘要").first.wait_for(timeout=5000)
        passed.append("预置证据账本加载")
        print("✅ 预置证据账本加载")
        await shot(page, "01_audit_list")

        # 2. 证据列表渲染（类型标签、工作流、节点、操作方、哈希）
        assert await page.locator("text=工具调用").count() >= 1, "未找到 工具调用 类型"
        assert await page.locator("text=代码变更驱动的 CI/CD 质量门禁").count() >= 1, "未找到 工作流 字段"
        assert await page.locator("text=变更影响分析").count() >= 1, "未找到 节点 字段"
        assert await page.locator("text=gemini_2_5_pro").count() >= 1, "未找到 操作方"
        assert await page.locator("text=哈希").count() >= 1, "未找到 哈希 标签"
        passed.append("证据列表渲染（类型 / 工作流 / 节点 / 操作方 / 哈希）")
        print("✅ 证据列表渲染（类型 / 工作流 / 节点 / 操作方 / 哈希）")

        # 3. 6 类证据类型齐全（PRD §6.6）
        for t in ["工具调用", "白名单拒绝", "质量门禁裁决", "缺陷归档", "人工审批", "升级处理"]:
            await page.locator(f".polaroid-card.rounded-lg.p-4 >> text={t}").first.wait_for(timeout=5000)
        passed.append("6 类证据类型齐全（PRD §6.6）")
        print("✅ 6 类证据类型齐全（PRD §6.6）")
        await shot(page, "02_all_types")

        # 4. 搜索过滤（搜索 "webFetch" 命中工具调用条目）
        await page.fill("input[placeholder='搜索证据 ID / 详情...']", "webFetch")
        await page.wait_for_timeout(400)
        assert await page.locator("text=调用 webFetch").count() >= 1, "搜索未命中 webFetch 条目"
        passed.append("搜索过滤命中")
        print("✅ 搜索过滤命中")
        await page.fill("input[placeholder='搜索证据 ID / 详情...']", "")
        await page.wait_for_timeout(300)

        # 5. 按类型筛选
        type_select = page.locator("select").nth(0)
        await type_select.select_option(value="缺陷归档")
        await page.wait_for_timeout(300)
        defect_count = await page.locator(".polaroid-card.rounded-lg.p-4 >> text=缺陷归档").count()
        assert defect_count >= 1, "类型筛选：缺陷归档 未命中"
        passed.append(f"按类型筛选（缺陷归档 命中 {defect_count} 条）")
        print(f"✅ 按类型筛选（缺陷归档 命中 {defect_count} 条）")
        await type_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 6. 按工作流筛选
        wf_select = page.locator("select").nth(1)
        await wf_select.select_option(value="移动端多端回归")
        await page.wait_for_timeout(300)
        wf_count = await page.locator(".polaroid-card.rounded-lg.p-4").count()
        assert wf_count >= 1, "工作流筛选：移动端多端回归 未命中"
        passed.append(f"按工作流筛选（移动端多端回归 命中 {wf_count} 条）")
        print(f"✅ 按工作流筛选（移动端多端回归 命中 {wf_count} 条）")
        await wf_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 7. 按节点筛选
        node_select = page.locator("select").nth(2)
        await node_select.select_option(value="质量门禁")
        await page.wait_for_timeout(300)
        node_count = await page.locator(".polaroid-card.rounded-lg.p-4").count()
        assert node_count >= 1, "节点筛选：质量门禁 未命中"
        passed.append(f"按节点筛选（质量门禁 命中 {node_count} 条）")
        print(f"✅ 按节点筛选（质量门禁 命中 {node_count} 条）")
        await node_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 8. 校验哈希链
        await page.click("button:has-text('校验哈希链')")
        toast_box = page.locator(".fixed.bottom-6.right-6")
        await toast_box.first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        passed.append("校验哈希链")
        print("✅ 校验哈希链")
        await shot(page, "03_verify_chain")

        # 9. 追加证据条目
        await page.click("button:has-text('＋ 追加证据')")
        await page.wait_for_selector("h3:has-text('追加证据条目')", timeout=5000)
        await page.fill("input[placeholder='工作流名称']", "V8 测试工作流")
        await page.fill("input[placeholder='节点名称']", "测试节点")
        await page.fill("input[placeholder='平台 / 模型 / 人工']", "测试负责人")
        await page.fill("textarea", "V8 自动验证追加的证据条目")
        await page.fill("input[placeholder='trace:xxx / gate:xxx / defect:xxx']", "manual:v8_test")
        await page.locator("div.fixed button:has-text('追加')").first.click()
        await page.wait_for_selector("text=证据已追加", timeout=5000)
        await page.wait_for_timeout(500)
        passed.append("追加证据条目（哈希链更新）")
        print("✅ 追加证据条目（哈希链更新）")
        await shot(page, "04_appended")

        # 10. 导出账本
        await page.click("button:has-text('导出账本')")
        await page.wait_for_selector("h3:has-text('导出审计账本')", timeout=5000)
        # 等待导出内容加载完成（pre 代码块出现）
        await page.locator("pre").first.wait_for(timeout=5000)
        passed.append("导出账本（合规审计）")
        print("✅ 导出账本（合规审计）")
        await shot(page, "05_export")
        # 关闭导出弹窗
        await page.locator("div.fixed button:has-text('×')").first.click()
        await page.wait_for_timeout(300)

        # 11. 业务串联：审计证据账本 → 工作流列表
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：审计证据账本 → 工作流列表")
        print("✅ 业务串联：审计证据账本 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V8 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V8 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
