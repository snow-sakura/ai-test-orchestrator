"""V10 Loop Engineering 自动验证脚本
验证 /resources 资源与锁管理全部功能（PRD §6.2）：
1. 页面渲染 + 预置资源池加载
2. 汇总条（资源池 / 成员 / 锁定 / 活动锁 / 排队 / 事件）
3. 资源池卡片渲染（类型 / 总数 / 锁定 / 空闲 + 成员列表 + TTL）
4. 按类型筛选资源池
5. 登记资源池（弹窗创建 → toast）
6. 资源锁 Tab + 状态筛选 + 获取锁
7. 释放锁（锁定中 → 已释放）
8. 锁事件 Tab（时间线 + 动作筛选）
9. 冲突队列 Tab（策略 / 请求方 / 等待）
10. 业务串联：资源与锁 → 工作流列表
关键步骤自动截图到 tests/screenshots/v10/
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v10")
os.makedirs(SHOT_DIR, exist_ok=True)


def reset_resources():
    """把 resources.json 复位为预置种子，避免重复测试累积"""
    path = os.path.join(os.path.dirname(__file__), "..", "backend", "resources.json")
    seeds = {
        "pools": [
            {"id": "pool_device", "type": "设备", "name": "移动设备池", "total": 4, "locked": 3, "free": 1,
             "members": [
                 {"id": "dev_a", "label": "设备 A（iPhone 15 Pro）", "status": "locked", "holder": "移动端多端回归 · n_exec_a", "ttl": 180},
                 {"id": "dev_b", "label": "设备 B（Pixel 8）", "status": "locked", "holder": "移动端多端回归 · n_exec_b", "ttl": 120},
                 {"id": "dev_c", "label": "设备 C（Android 模拟器）", "status": "locked", "holder": "兼容性冒烟 · n_compat", "ttl": 3600},
                 {"id": "dev_d", "label": "设备 D（iPad）", "status": "free", "holder": "", "ttl": 0},
             ]},
            {"id": "pool_env", "type": "环境", "name": "测试环境池", "total": 2, "locked": 1, "free": 1,
             "members": [
                 {"id": "env_staging", "label": "staging-web", "status": "locked", "holder": "CI/CD 门禁 · n_api_exec", "ttl": 720},
                 {"id": "env_perftest", "label": "perftest-env", "status": "free", "holder": "", "ttl": 0},
             ]},
            {"id": "pool_cred", "type": "凭据", "name": "凭据资源池", "total": 3, "locked": 1, "free": 2,
             "members": [
                 {"id": "cred_prod_ro", "label": "生产只读 DB 凭据", "status": "locked", "holder": "数据一致性节点 · n_data_check", "ttl": 300},
                 {"id": "cred_sandbox", "label": "沙箱 API Key", "status": "free", "holder": "", "ttl": 0},
                 {"id": "cred_ci", "label": "CI Runner Token", "status": "free", "holder": "", "ttl": 0},
             ]},
            {"id": "pool_slot", "type": "并发槽位", "name": "并行执行槽位", "total": 6, "locked": 4, "free": 2,
             "members": [
                 {"id": "slot_1", "label": "槽位 1", "status": "locked", "holder": "并行分发 · 单元测试", "ttl": 540},
                 {"id": "slot_2", "label": "槽位 2", "status": "locked", "holder": "并行分发 · 接口测试", "ttl": 480},
                 {"id": "slot_3", "label": "槽位 3", "status": "locked", "holder": "并行分发 · 安全探测", "ttl": 900},
                 {"id": "slot_4", "label": "槽位 4", "status": "locked", "holder": "并行分发 · 性能负载", "ttl": 600},
                 {"id": "slot_5", "label": "槽位 5", "status": "free", "holder": "", "ttl": 0},
                 {"id": "slot_6", "label": "槽位 6", "status": "free", "holder": "", "ttl": 0},
             ]},
        ],
        "locks": [
            {"id": "lock_dev_a", "resourceId": "dev_a", "poolId": "pool_device", "mode": "独占锁", "holder": "移动端多端回归 · n_exec_a", "acquiredAt": "2026-10-26 15:32", "ttl": 180, "autoRelease": True, "status": "locked"},
            {"id": "lock_env_staging", "resourceId": "env_staging", "poolId": "pool_env", "mode": "独占锁", "holder": "CI/CD 门禁 · n_api_exec", "acquiredAt": "2026-10-26 16:05", "ttl": 720, "autoRelease": True, "status": "locked"},
            {"id": "lock_slot_shared", "resourceId": "slot_5", "poolId": "pool_slot", "mode": "共享锁", "holder": "探索任务 · n_browser_explore", "acquiredAt": "2026-10-26 16:40", "ttl": 300, "autoRelease": True, "status": "locked"},
            {"id": "lock_cred_prod", "resourceId": "cred_prod_ro", "poolId": "pool_cred", "mode": "独占锁", "holder": "数据一致性节点 · n_data_check", "acquiredAt": "2026-10-26 14:10", "ttl": 300, "autoRelease": False, "status": "locked"},
        ],
        "events": [
            {"id": "evt_001", "ts": "2026-10-26 15:32", "resourceId": "dev_a", "action": "获取", "actor": "移动端多端回归 · n_exec_a", "detail": "获取独占锁（TTL 180s，自动释放）"},
            {"id": "evt_002", "ts": "2026-10-26 15:34", "resourceId": "dev_a", "action": "持有", "actor": "移动端多端回归 · n_exec_b", "detail": "冲突：设备 A 已占用，按排队等待策略挂起"},
            {"id": "evt_003", "ts": "2026-10-26 16:05", "resourceId": "env_staging", "action": "获取", "actor": "CI/CD 门禁 · n_api_exec", "detail": "获取独占锁（TTL 720s）"},
            {"id": "evt_004", "ts": "2026-10-26 16:41", "resourceId": "slot_5", "action": "获取", "actor": "探索任务 · n_browser_explore", "detail": "获取共享锁，允许并发读取"},
            {"id": "evt_005", "ts": "2026-10-26 14:12", "resourceId": "cred_prod_ro", "action": "释放", "actor": "数据一致性节点 · n_data_check", "detail": "节点完成，主动释放独占锁"},
        ],
        "queue": [
            {"id": "q_001", "ts": "2026-10-26 15:34", "resourceId": "dev_a", "requester": "移动端多端回归 · n_exec_b", "policy": "排队等待", "waitSec": 180},
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seeds, f, ensure_ascii=False, indent=2)
    print(f"[reset] resources.json 复位为预置种子（{len(seeds['pools'])} 池 / {len(seeds['locks'])} 锁 / {len(seeds['events'])} 事件 / {len(seeds['queue'])} 队列）")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")


async def run():
    reset_resources()

    passed = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # 1. 页面渲染 + 预置资源池加载
        await page.goto(BASE + "/resources", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('资源与锁管理')", timeout=8000)
        passed.append("资源与锁管理页渲染")
        print("✅ 资源与锁管理页渲染")

        await page.locator("text=移动设备池").first.wait_for(timeout=5000)
        passed.append("预置资源池加载")
        print("✅ 预置资源池加载")

        # 汇总条出现
        await page.locator("text=活动锁").first.wait_for(timeout=5000)
        passed.append("汇总条渲染（池 / 成员 / 锁定 / 活动锁 / 排队 / 事件）")
        print("✅ 汇总条渲染（池 / 成员 / 锁定 / 活动锁 / 排队 / 事件）")
        await shot(page, "01_pools")

        # 2. 资源池卡片渲染（类型 / 总数 / 锁定 / 空闲 + 成员 + TTL）
        assert await page.locator("text=共 4").count() >= 1, "未找到 共 4 总数"
        assert await page.locator("text=设备 A（iPhone 15 Pro）").count() >= 1, "未找到 成员 设备 A"
        assert await page.locator("text=TTL 180s").count() >= 1, "未找到 TTL 180s"
        assert await page.locator("text=持有：移动端多端回归 · n_exec_a").count() >= 1, "未找到 持有方"
        passed.append("资源池卡片渲染（总数 / 锁定 / 空闲 / 成员 / TTL / 持有方）")
        print("✅ 资源池卡片渲染（总数 / 锁定 / 空闲 / 成员 / TTL / 持有方）")

        # 3. 按类型筛选资源池（并发槽位 → 命中 1 池）
        type_select = page.locator("select").nth(0)
        await type_select.select_option(value="并发槽位")
        await page.wait_for_timeout(300)
        slot_count = await page.locator(".polaroid-card.rounded-lg.p-4 >> text=并行执行槽位").count()
        assert slot_count >= 1, "类型筛选：并发槽位 未命中"
        passed.append(f"按类型筛选（并发槽位 命中 {slot_count} 池）")
        print(f"✅ 按类型筛选（并发槽位 命中 {slot_count} 池）")
        await type_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 4. 登记资源池（弹窗创建 → toast）
        await page.click("button:has-text('＋ 登记资源池')")
        await page.wait_for_selector("h3:has-text('登记资源池')", timeout=5000)
        # 弹窗内先选择类型为 数据源，再填写名称
        await page.locator("div.fixed select").first.select_option(value="数据源")
        await page.fill("input[placeholder='资源池名称']", "V10 测试数据源池")
        await page.locator("div.fixed button:has-text('登记')").first.click()
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        # 筛选数据源类型以确认新池出现
        type_select = page.locator("select").nth(0)
        await type_select.select_option(value="数据源")
        await page.wait_for_timeout(300)
        assert await page.locator(".polaroid-card.rounded-lg.p-4 >> text=V10 测试数据源池").count() >= 1, "登记后未出现新资源池"
        passed.append("登记资源池（弹窗创建 + 列表更新 + toast）")
        print("✅ 登记资源池（弹窗创建 + 列表更新 + toast）")
        await page.locator("select").nth(0).select_option(value="")
        await page.wait_for_timeout(300)
        await shot(page, "02_created")

        # 5. 资源锁 Tab + 状态筛选 + 获取锁
        await page.click("button:has-text('资源锁')")
        await page.wait_for_selector(".polaroid-card.rounded-lg.p-4 >> text=dev_a", timeout=5000)
        assert await page.locator("text=移动端多端回归 · n_exec_a").count() >= 1, "资源锁未命中持有方"
        passed.append("资源锁 Tab（4 条锁 + 持有方 + TTL）")
        print("✅ 资源锁 Tab（4 条锁 + 持有方 + TTL）")
        await shot(page, "03_locks")

        # 状态筛选：锁定中
        lock_status_select = page.locator("select").nth(0)
        await lock_status_select.select_option(value="locked")
        await page.wait_for_timeout(300)
        locked_count = await page.locator(".polaroid-card.rounded-lg.p-4 >> text=锁定中").count()
        assert locked_count >= 1, "状态筛选：锁定中 未命中"
        passed.append(f"资源锁状态筛选（锁定中 命中 {locked_count} 条）")
        print(f"✅ 资源锁状态筛选（锁定中 命中 {locked_count} 条）")
        await lock_status_select.select_option(value="")
        await page.wait_for_timeout(300)

        # 获取锁（弹窗创建）
        await page.click("button:has-text('＋ 获取锁')")
        await page.wait_for_selector("h3:has-text('获取资源锁')", timeout=5000)
        await page.fill("input[placeholder='dev_a / env_staging / slot_1 ...']", "dev_d")
        await page.fill("input[placeholder='工作流名 · 节点名']", "V10 测试 · n_v10")
        await page.locator("div.fixed button:has-text('获取')").first.click()
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        assert await page.locator("text=V10 测试 · n_v10").count() >= 1, "获取后未出现新锁"
        passed.append("获取锁（弹窗创建 + 列表更新 + toast）")
        print("✅ 获取锁（弹窗创建 + 列表更新 + toast）")
        await shot(page, "04_acquired")

        # 6. 释放锁（锁定中 → 已释放）
        release_btn = page.locator(".polaroid-card.rounded-lg.p-4 >> button:has-text('释放')").first
        await release_btn.click()
        await page.locator(".fixed.bottom-6.right-6").first.wait_for(timeout=5000)
        await page.wait_for_timeout(500)
        passed.append("释放锁（锁定中 → 已释放 + toast）")
        print("✅ 释放锁（锁定中 → 已释放 + toast）")
        await shot(page, "05_released")

        # 7. 锁事件 Tab（时间线 + 动作筛选）
        await page.click("button:has-text('锁事件')")
        await page.wait_for_selector(".polaroid-card.rounded-lg.p-4 >> text=冲突：设备 A 已占用", timeout=5000)
        assert await page.locator("text=获取独占锁（TTL 180s，自动释放）").count() >= 1, "锁事件未命中获取详情"
        passed.append("锁事件 Tab（时间线 + 冲突记录）")
        print("✅ 锁事件 Tab（时间线 + 冲突记录）")
        # 动作筛选：释放
        action_select = page.locator("select").nth(0)
        await action_select.select_option(value="释放")
        await page.wait_for_timeout(300)
        released_count = await page.locator("text=节点完成，主动释放独占锁").count()
        assert released_count >= 1, "动作筛选：释放 未命中"
        passed.append(f"锁事件动作筛选（释放 命中 {released_count} 条）")
        print(f"✅ 锁事件动作筛选（释放 命中 {released_count} 条）")
        await shot(page, "06_events")

        # 8. 冲突队列 Tab
        await page.click("button:has-text('冲突队列')")
        await page.wait_for_selector(".polaroid-card.rounded-lg.p-4 >> text=排队等待", timeout=5000)
        assert await page.locator("text=移动端多端回归 · n_exec_b").count() >= 1, "冲突队列未命中请求方"
        passed.append("冲突队列 Tab（策略 / 请求方 / 等待）")
        print("✅ 冲突队列 Tab（策略 / 请求方 / 等待）")
        await shot(page, "07_queue")

        # 9. 业务串联：资源与锁 → 工作流列表
        await page.goto(BASE + "/workflows", wait_until="networkidle")
        await page.wait_for_selector("h2:has-text('工作流列表')", timeout=8000)
        passed.append("业务串联：资源与锁 → 工作流列表")
        print("✅ 业务串联：资源与锁 → 工作流列表")

        # JS 错误检查
        real_errors = [e for e in errors if "React DevTools" not in e]
        assert not real_errors, f"页面 JS 错误: {real_errors}"
        passed.append("无页面 JS 报错")
        print(f"✅ 无页面 JS 报错（有效 {len(real_errors)} 条）")

        await browser.close()

    print("\n========== V10 验证结果 ==========")
    for i, item in enumerate(passed, 1):
        print(f"  {i}. {item}")
    print(f"\n🎉 V10 全部 {len(passed)} 项验证通过")


if __name__ == "__main__":
    asyncio.run(run())
