# -*- coding: utf-8 -*-
"""
V15 全量精确走查脚本（竞品排版对齐 + Agnes AI 配置 + 登录守卫 + 1920×1080 适配）。

本脚本：
  1. reset_all_seeds() 复位 9 个 JSON 数据源（Agnes-only 模型注册表 + 三层配置）；
  2. 打开真实有头浏览器（headless=False, viewport 1920×1080），逐页精确断言
     竞品排版（#001529 侧栏 / #1890ff 主色 / #f5f5f5 主区 / 24px 页标题 / 卡片容器），
     每个菜单后 sleep 800ms；
  3. 登录守卫验证：未登录 → /login；登录后 → /dashboard；
  4. 1920×1080 不溢出：documentElement.scrollHeight ≤ 1080，内容区 fixed-height + overflow-y:auto；
  5. Agnes AI 配置断言：注册表仅 Agnes、三层配置参数、baseUrl/envKey、明文密钥泄露守卫；
  6. JS 报错检查；截图到 tests/screenshots/v15/；
  7. 结尾打印「通过 N · 失败 M」。

运行（系统 python3，Playwright 已装）：
  python3 tests/v15_full_walkthrough.py
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5173"
BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
SHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots", "v15")
os.makedirs(SHOT_DIR, exist_ok=True)

PAUSE = 800  # 适中停顿（ms）：每次断言后 sleep
SHOT_PAUSE = 500  # 截图前后停顿

# 明文密钥（仅用于泄露守卫断言：UI 不得渲染）
PLAINTEXT_KEY = "sk-E5A4BXwmPvyYXccHiaFleQbcvTBKkk5rBHbC58R2zabgJriV"
MASKED_KEY = "sk-E5A4••••••••2zabgJriV"


def _w(name, data):
    with open(os.path.join(BACKEND, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def reset_all_seeds():
    """把 9 个 JSON 数据源复位（Agnes-only 模型注册表 + 三层配置 + 基础业务数据）。"""
    _w("workflows.json", {"default-workflow": {
        "id": "default-workflow", "name": "我的第一个测试工作流", "status": "draft",
        "nodes": [
            {"id": "n1", "label": "开始", "type": "platform", "position": {"x": 80, "y": 120}, "config": {}},
            {"id": "n2", "label": "需求解析", "type": "analysis", "position": {"x": 320, "y": 120}, "config": {"model": "Agnes 3.0 Flash"}},
            {"id": "n3", "label": "结束", "type": "platform", "position": {"x": 560, "y": 120}, "config": {}},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ],
    }})
    _w("runs.json", {"run_001": {
        "id": "run_001", "workflow_id": "default-workflow", "workflow_name": "我的第一个测试工作流",
        "status": "success", "started_at": "2026-10-28T09:00:00", "finished_at": "2026-10-28T09:05:00",
        "timeline": [
            {"node_id": "n1", "label": "开始", "status": "success", "output": {}},
            {"node_id": "n2", "label": "需求解析", "status": "success", "output": {"model": "Agnes 3.0 Flash", "summary": "解析完成"}},
            {"node_id": "n3", "label": "结束", "status": "success", "output": {}},
        ],
    }})
    _w("assets.json", {"asset_001": {
        "id": "asset_001", "name": "回归用例集", "type": "用例", "version": "v1.0",
        "quality": "已认证", "updated_at": "2026-10-28",
    }})
    _w("tasks.json", {"task_001": {
        "id": "task_001", "name": "全链路回归", "status": "进行中", "progress": 60,
        "created_at": "2026-10-28", "assignee": "测试负责人",
    }})
    _w("models.json", {
        "registry": [{
            "id": "agnes_3_0_flash", "name": "Agnes 3.0 Flash", "vendor": "Agnes", "kind": "文本",
            "tier": "高", "context": "128K", "dailyLimit": 2000,
            "pricePerMIn": 0.01, "pricePerMOut": 0.04,
            "desc": "高速推理文本模型，128K 上下文",
        }],
        "configs": {
            "global": {
                "level": "全站", "owner": "", "textModel": "agnes_3_0_flash", "visionModel": "",
                "textModelName": "Agnes 3.0 Flash", "visionModelName": "",
                "params": {"temperature": 0.2, "maxTokens": 128000},
                "keyMasked": MASKED_KEY, "keyMaskedSource": "CHERRY_QWEN_API_KEY",
                "baseUrl": "https://apihub.agnes-ai.com/v1", "envKey": "CHERRY_QWEN_API_KEY",
                "connected": True,
            },
        },
        "grants": [], "quotas": [
            {"model": "agnes_3_0_flash", "modelName": "Agnes 3.0 Flash",
             "dailyLimit": 2000, "usedToday": 120, "extraToday": 0, "available": 1880, "usedRatio": 6},
        ], "usage": [],
    })
    _w("capabilities.json", {"caps": [
        {"id": "cap_001", "name": "用例生成", "status": "已授权"},
        {"id": "cap_002", "name": "多端执行", "status": "已授权"},
    ], "calls": [], "approvals": [], "connects": []})
    _w("resources.json", {"pools": [
        {"id": "pool_001", "name": "默认资源池", "members": ["node-a", "node-b"], "capacity": 10, "used": 3},
    ], "locks": [], "events": [], "queue": []})
    _w("audit.json", {"events": [
        {"id": "ev_001", "ts": "2026-10-28T09:00:00", "actor": "agnes_3_0_flash",
         "action": "run.start", "workflow": "default-workflow", "prevHash": "0" * 64, "hash": "abc123"},
    ]})
    _w("settings.json", {
        "sections": [
            {"key": "驱动", "title": "驱动引擎", "items": [
                {"key": "默认文本模型", "value": "Agnes 3.0 Flash", "options": ["Agnes 3.0 Flash"]},
                {"key": "推理温度", "value": 0.2},
                {"key": "Top-P", "value": 0.9},
                {"key": "最大 Token 数", "value": 128000},
            ]},
        ],
        "budgets": [
            {"key": "budget_node", "name": "节点预算", "limit": 500},
            {"key": "budget_workflow", "name": "工作流预算", "limit": 5000},
            {"key": "budget_platform", "name": "平台预算", "limit": 50000},
        ],
    })
    print("[reset] 9 个 JSON 数据源已复位（Agnes-only 模型注册表 + 三层配置）")


_OK = 0
_FAIL = 0


def check(cond, msg):
    global _OK, _FAIL
    if cond:
        _OK += 1
        print(f"  ✅ {msg}")
    else:
        _FAIL += 1
        print(f"  ❌ {msg}")


async def shot(page, name):
    await page.screenshot(path=os.path.join(SHOT_DIR, name + ".png"))
    print(f"  [screenshot] {name}.png")
    await page.wait_for_timeout(SHOT_PAUSE)


async def pause(page, ms=PAUSE):
    await page.wait_for_timeout(ms)


# 竞品视觉规格（testhub_platform-main 对齐）
COMPETITOR_NAVY_RGB = "rgb(0, 21, 41)"      # #001529
COMPETITOR_MAIN_RGB = "rgb(245, 245, 245)"   # #f5f5f5


async def check_competitor_layout(page, route):
    """断言竞品排版：#001529 侧栏 / #1890ff 主色 / #f5f5f5 主区 / 24px 页标题 / 卡片容器。"""
    # 侧栏背景 navy
    sidebar_bg = await page.evaluate(
        "() => { const a = document.querySelector('aside'); return a ? getComputedStyle(a).backgroundColor : ''; }"
    )
    check(sidebar_bg == COMPETITOR_NAVY_RGB, f"{route} 侧栏背景 #001529（{sidebar_bg}）")
    # 主区背景
    main_bg = await page.evaluate(
        "() => { const m = document.querySelector('.page-container'); return m ? getComputedStyle(m).backgroundColor : ''; }"
    )
    check(main_bg == COMPETITOR_MAIN_RGB, f"{route} 主区背景 #f5f5f5（{main_bg}）")
    # 页标题
    pt_size = await page.evaluate(
        "() => { const t = document.querySelector('.page-title'); return t ? getComputedStyle(t).fontSize : ''; }"
    )
    check(pt_size == "24px", f"{route} 页标题 24px（{pt_size}）")
    # 卡片容器（card-container 或 polaroid-card）
    card = await page.locator(".card-container, .polaroid-card").count()
    check(card >= 1, f"{route} 卡片容器可见（{card}）")
    # 无明文密钥泄露
    body = await page.inner_text("body")
    check(PLAINTEXT_KEY not in body, f"{route} 无明文密钥泄露")


async def check_no_overflow_1920(page):
    """1920×1080 不溢出：documentElement.scrollHeight ≤ 1080。"""
    sh = await page.evaluate("() => document.documentElement.scrollHeight")
    check(sh <= 1080, f"1920×1080 不溢出（documentElement.scrollHeight={sh} ≤ 1080）")


async def check_content_scroll(page):
    """内容区 fixed-height + overflow-y:auto。"""
    has_scroll = await page.evaluate(
        "() => { const m = document.querySelector('.page-container'); "
        "return m ? getComputedStyle(m).overflowY : ''; }"
    )
    check(has_scroll in ("auto", "scroll"), f"内容区 overflow-y（{has_scroll}）")


async def check_agnes_config(page):
    """Agnes AI 配置断言：注册表仅 Agnes、三层配置参数、baseUrl/envKey。"""
    # 注册表仅 Agnes
    reg_count = await page.evaluate(
        "() => fetch('/api/models/registry').then(r => r.json()).then(d => Array.isArray(d) ? d.length : 0)"
    )
    check(reg_count == 1, f"模型注册表仅 1 个（Agnes-only，实际 {reg_count}）")
    # 三层配置可见
    configs = await page.evaluate(
        "() => fetch('/api/models/configs').then(r => r.json()).then(d => d)"
    )
    cfg_list = configs if isinstance(configs, list) else list(configs.values())
    check(len(cfg_list) >= 1, f"三层配置可见（{len(cfg_list)}）")
    if cfg_list:
        c = cfg_list[0]
        check(c.get("textModelName") == "Agnes 3.0 Flash", "三层配置文本模型 Agnes 3.0 Flash")
        check(c.get("params", {}).get("temperature") == 0.2, "三层配置 temperature 0.2")
        check(c.get("params", {}).get("maxTokens") == 128000, "三层配置 maxTokens 128000")
        check(c.get("keyMasked") == MASKED_KEY, "三层配置密钥掩码可见")
        check("sk-E5A4" in (c.get("keyMasked") or ""), "掩码 sk-E5A4 可见")
        check(PLAINTEXT_KEY not in json.dumps(c, ensure_ascii=False), "三层配置无明文密钥")
        check(c.get("baseUrl") == "https://apihub.agnes-ai.com/v1", "端点 baseUrl agnes")
        check(c.get("envKey") == "CHERRY_QWEN_API_KEY", "密钥来源 envKey CHERRY_QWEN_API_KEY")


async def run():
    global _OK, _FAIL
    reset_all_seeds()
    _OK = 0
    _FAIL = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--no-default-browser-check"])

        # ── 页面 A：无 init script，验证登录守卫 ──
        page_a = await browser.new_page(viewport={"width": 1920, "height": 1080})
        errors_a = []
        page_a.on("pageerror", lambda e: errors_a.append(str(e)))
        print("🌐 有头浏览器已打开（1920×1080）· V15 全量精确走查开始\n")

        print("── ① 登录守卫（未登录 → /login）──")
        await page_a.goto(BASE + "/dashboard", wait_until="networkidle")
        # 未登录：router.beforeEach 将 /dashboard 重定向到 /login
        await page_a.wait_for_selector("text=欢迎登录", timeout=10000)
        check("/login" in page_a.url or "欢迎登录" in await page_a.inner_text("body"),
              "未登录访问 /dashboard → 重定向 /login")
        check(await page_a.locator(".card-container").count() >= 1, "/login 卡片容器可见")
        check(await page_a.locator("text=智能编排").count() >= 1, "/login 品牌能力徽章（智能编排）可见")
        check(await page_a.locator("text=Agnes 模型").count() >= 1, "/login 品牌能力徽章（Agnes 模型）可见")
        check(await page_a.locator("text=认证资产").count() >= 1, "/login 品牌能力徽章（认证资产）可见")
        check(await page_a.locator("text=审计账本").count() >= 1, "/login 品牌能力徽章（审计账本）可见")
        await pause(page_a)
        await shot(page_a, "01_login")

        # 通过登录表单登录（输入账号 → 提交），验证 onLogin 跳转 /dashboard
        print("\n── ① 登录表单 → /dashboard ──")
        await page_a.locator("input[placeholder='测试负责人']").fill("测试负责人")
        await page_a.locator("input[type='password']").fill("123456")
        await page_a.locator("button[type='submit']").click()
        await page_a.wait_for_url("**/dashboard", timeout=10000)
        check("/dashboard" in page_a.url, "登录后跳转 /dashboard")
        # 验证 localStorage 已写入
        has_auth = await page_a.evaluate("localStorage.getItem('aio_auth')")
        check(has_auth is not None, "登录后 localStorage aio_auth 已写入")
        await pause(page_a)
        await shot(page_a, "01b_after_login")
        await page_a.close()

        # ── 页面 B：有 init script（预置已登录态），走全量功能页 ──
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.add_init_script(
            "localStorage.setItem('aio_auth', JSON.stringify({name:'雪 樱',role:'测试负责人',avatar:'雪',lastLoginAt:'2026-10-28'}))"
        )
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ② 登录后 → /dashboard
        print("\n── ② 工作台总览（登录后首页）──")
        await page.goto(BASE + "/dashboard", wait_until="networkidle")
        await page.wait_for_selector("text=工作台总览", timeout=10000)
        check("工作台总览" in page.url or await page.locator("text=工作台总览").count() >= 1, "登录后 /dashboard 可达")
        await check_competitor_layout(page, "/dashboard")
        await check_no_overflow_1920(page)
        await check_content_scroll(page)
        await pause(page)
        await shot(page, "02_dashboard")

        # ③ 逐页精确断言（11 功能页 + dashboard 已含），每页停顿
        print("\n── ③ 逐菜单精确走查（竞品排版 + 停顿 800ms）──")
        for route, wait_sel in [
            ("/workflows", "text=工作流列表"),
            ("/editor", "text=节点模板库"),
            ("/runs", "text=执行追踪"),
            ("/assets", "text=认证资产库"),
            ("/tasks", "text=异步任务看板"),
            ("/models", "text=模型与额度"),
            ("/audit", "text=审计证据账本"),
            ("/capabilities", "text=开放能力控制台"),
            ("/resources", "text=资源与锁管理"),
            ("/settings", "text=统一配置中心"),
        ]:
            print(f"  · 进入 {route}")
            await page.goto(BASE + route, wait_until="networkidle")
            await page.wait_for_selector(wait_sel, timeout=10000)
            await pause(page)
            # 竞品排版（editor 为画布页，无 .page-container，单独处理）
            if route == "/editor":
                # editor 画布：节点库 + 画布主体
                check(await page.locator("text=节点模板库").count() >= 1, "editor 节点库可见")
                check(await page.locator(".vue-flow").count() >= 1, "editor VueFlow 画布可见")
                # 点击画布节点打开配置抽屉，展开「模型配置」分区，验证模型下拉仅 Agnes
                await page.locator(".vue-flow .vue-flow__node").first.click()
                await page.wait_for_selector("text=节点配置", timeout=8000)
                # 展开抽屉内的「模型配置」折叠分区
                await page.locator("text=模型配置").first.click()
                await page.wait_for_selector("text=选择模型", timeout=8000)
                model_opts = await page.locator("select option").all_inner_texts()
                check(any("Agnes 3.0 Flash" in t for t in model_opts), "editor 模型下拉含 Agnes 3.0 Flash")
                body = await page.inner_text("body")
                check(PLAINTEXT_KEY not in body, "editor 无明文密钥泄露")
            else:
                await check_competitor_layout(page, route)
                await check_no_overflow_1920(page)
                await check_content_scroll(page)
            # Agnes 配置断言（仅 models 页）
            if route == "/models":
                await check_agnes_config(page)
            await shot(page, f"{route.strip('/')}")

        # ④ Agnes 注册表全局守卫（任意页）
        print("\n── ④ Agnes 注册表全局守卫 ──")
        reg_names = await page.evaluate(
            "() => fetch('/api/models/registry').then(r => r.json()).then(d => Array.isArray(d) ? d.map(m => m.name) : [])"
        )
        check(len(reg_names) == 1 and reg_names[0] == "Agnes 3.0 Flash", f"注册表仅 Agnes（{reg_names}）")
        check("Claude" not in " ".join(reg_names) and "GPT" not in " ".join(reg_names),
              "注册表无 Claude/GPT 等非 Agnes 模型")

        # ⑤ JS 报错检查（合并页面 A + B）
        all_errors = errors_a + errors
        print("\n── ⑤ JS 报错检查 ──")
        check(len(all_errors) == 0, f"无 JS 报错（{len(all_errors)}）")
        if all_errors:
            print("   报错明细：")
            for e in all_errors[:5]:
                print(f"   - {e}")

        print(f"\n══════ V15 全量走查完成：通过 {_OK} · 失败 {_FAIL} ══════")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
