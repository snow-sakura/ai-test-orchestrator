/* ==========================================================================
   编排画布引擎
   - 图形模型 / 渲染 / 拖拽 / 连线 / 缩放平移 / 缩略图
   - 撤销重做 / 复制粘贴 / 框选 / 自动保存
   - 结构校验 / 试运行模拟
   ========================================================================== */
(function () {
  'use strict';

  const NODE_W = 176, NODE_H = 56;

  /* ------------------------------------------------------------------
     1. 默认图（对应 PRD §8.1 代码变更驱动的 CI/CD 质量门禁范式）
     ------------------------------------------------------------------ */
  const DEFAULT_GRAPH = {
    wfId: 'wf_cicd',
    name: '代码变更驱动的 CI/CD 质量门禁',
    status: 'published',
    nodes: [
      { id: 'n_start', type: 'start', x: 40, y: 300 },
      { id: 'n_impact', type: 'impact_analysis', x: 250, y: 300 },
      { id: 'n_risk', type: 'risk_rating', x: 460, y: 300 },
      { id: 'n_gen', type: 'code_change_gen', x: 670, y: 300 },
      { id: 'n_gate', type: 'plan_gate', x: 880, y: 300, aux: true },
      { id: 'n_par', type: 'parallel', x: 1090, y: 300 },
      { id: 'n_unit', type: 'unit_test_gen', x: 1330, y: 150 },
      { id: 'n_api', type: 'api_test', x: 1330, y: 250 },
      { id: 'n_sec', type: 'security_scan', x: 1330, y: 350 },
      { id: 'n_perf', type: 'perf_test', x: 1330, y: 450 },
      { id: 'n_join', type: 'join', x: 1570, y: 300, aux: true },
      { id: 'n_triage', type: 'triage', x: 1800, y: 300, aux: true },
      { id: 'n_cond', type: 'condition', x: 2030, y: 300, aux: true },
      { id: 'n_repro', type: 'reproduce', x: 2260, y: 190, aux: true },
      { id: 'n_root', type: 'root_cause', x: 2490, y: 190, aux: true },
      { id: 'n_heal', type: 'self_heal', x: 2260, y: 410, aux: true },
      { id: 'n_retry', type: 'retry', x: 2490, y: 410, aux: true },
      { id: 'n_qgate', type: 'quality_gate', x: 2720, y: 300 },
      { id: 'n_report', type: 'report_gen', x: 2950, y: 300 },
      { id: 'n_end', type: 'end', x: 3180, y: 300 },
    ],
    edges: [
      { id: 'e1', from: 'n_start', to: 'n_impact' },
      { id: 'e2', from: 'n_impact', to: 'n_risk' },
      { id: 'e3', from: 'n_risk', to: 'n_gen' },
      { id: 'e4', from: 'n_gen', to: 'n_gate' },
      { id: 'e5', from: 'n_gate', to: 'n_par' },
      { id: 'e6', from: 'n_par', to: 'n_unit' },
      { id: 'e7', from: 'n_par', to: 'n_api' },
      { id: 'e8', from: 'n_par', to: 'n_sec' },
      { id: 'e9', from: 'n_par', to: 'n_perf' },
      { id: 'e10', from: 'n_unit', to: 'n_join' },
      { id: 'e11', from: 'n_api', to: 'n_join' },
      { id: 'e12', from: 'n_sec', to: 'n_join' },
      { id: 'e13', from: 'n_perf', to: 'n_join' },
      { id: 'e14', from: 'n_join', to: 'n_triage' },
      { id: 'e15', from: 'n_triage', to: 'n_cond' },
      { id: 'e16', from: 'n_cond', to: 'n_repro', label: '产品缺陷' },
      { id: 'e17', from: 'n_cond', to: 'n_heal', label: '测试问题' },
      { id: 'e18', from: 'n_repro', to: 'n_root' },
      { id: 'e19', from: 'n_heal', to: 'n_retry' },
      { id: 'e20', from: 'n_root', to: 'n_qgate' },
      { id: 'e21', from: 'n_retry', to: 'n_qgate' },
      { id: 'e22', from: 'n_qgate', to: 'n_report' },
      { id: 'e23', from: 'n_report', to: 'n_end' },
    ],
  };

  /* ------------------------------------------------------------------
     2. 节点默认配置生成
     ------------------------------------------------------------------ */
  const MODEL_POOL = ['GPT-4o', 'Claude Sonnet 4', 'Qwen-Max', 'DeepSeek-V3', 'Qwen2.5-VL-72B'];
  const TOOL_POOL = {
    design: ['req.doc.parse', 'case.template.render', 'asset.library.search', 'spec.parser'],
    execute: ['http.client', 'browser.driver', 'vision.ocr', 'device.control', 'perf.runner'],
    diagnose: ['log.search', 'trace.query', 'repo.diff', 'patch.apply'],
    quality: ['rule.engine', 'report.render', 'defect.tracker.write', 'kb.retrieve'],
    control: ['workflow.runtime', 'expr.evaluate'],
    base: ['http.client', 'mcp.invoke', 'sandbox.exec', 'data.factory'],
  };

  function defaultCfg(type) {
    const meta = ALL_NODES[type] || { out: [] };
    const cat = meta.cat || 'base';
    const outs = meta.out || [];
    const t = {
      name: meta.name || type,
      desc: meta.desc || '',
      icon: meta.icon || '◻',
      model: MODEL_POOL[Math.abs(hash(type)) % MODEL_POOL.length],
      temperature: cat === 'control' || cat === 'base' ? 0 : 0.3,
      topP: 0.9,
      systemPrompt: '',
      userPrompt: '',
      inputs: [],
      schema: outs.map(o => ({ key: o, type: 'string', required: true, evidence: false })),
      tools: (TOOL_POOL[cat] || []).slice(0, 3),
      deniedTools: ['shell.exec', 'fs.write'],
      skills: [],
      maxSteps: cat === 'execute' ? 30 : 12,
      timeout: cat === 'execute' ? 300 : 120,
      tokenBudget: cat === 'execute' ? 120000 : 40000,
      retry: 2,
      backoff: 'exponential',
      rules: [],
      async: type === 'async_task',
      resource: type === 'airtest' ? '设备池 · 独占锁' : '',
      resourceCount: 1,
      evidenceRequired: ['quality_gate', 'asset_certify', 'defect_archive', 'triage', 'reproduce',
        'root_cause', 'self_heal', 'asset_version', 'contract_check'].includes(type),
    };
    if (type === 'self_heal') {
      t.schema = [
        { key: 'fix_type', type: 'string', required: true, evidence: false },
        { key: 'changes', type: 'array', required: true, evidence: false },
        { key: 'risk', type: 'string', required: true, evidence: false },
        { key: 'evidence', type: 'array', required: true, evidence: true },
        { key: 'verify_plan', type: 'array', required: false, evidence: false },
      ];
    }
    if (type === 'asset_version') {
      t.schema = [
        { key: 'impact', type: 'array', required: true, evidence: false },
        { key: 'regression', type: 'array', required: true, evidence: false },
        { key: 'verdict', type: 'string', required: true, evidence: true },
      ];
    }
    if (type === 'start') {
      t.systemPrompt = '定义本次流水线触发所需的初始参数，作为工作流入口契约。';
      t.inputs = [
        { key: 'repo_url', from: '手动输入', type: 'string' },
        { key: 'base_branch', from: '手动输入', type: 'string' },
        { key: 'changed_files', from: 'Git Diff', type: 'array' },
      ];
      t.schema = [{ key: 'params', type: 'object', required: true, evidence: false }];
    } else if (type === 'end') {
      t.schema = [{ key: 'result', type: 'object', required: true, evidence: false }];
    } else if (type === 'triage') {
      t.schema = [
        { key: 'classification', type: 'string', required: true, evidence: false },
        { key: 'confidence', type: 'number', required: true, evidence: false },
        { key: 'basis', type: 'array', required: true, evidence: true },
        { key: 'routing', type: 'string', required: true, evidence: false },
      ];
    } else if (type === 'root_cause') {
      t.schema = [
        { key: 'hypothesis', type: 'string', required: true, evidence: false },
        { key: 'confidence', type: 'number', required: true, evidence: false },
        { key: 'component', type: 'string', required: true, evidence: false },
        { key: 'evidence', type: 'array', required: true, evidence: true },
      ];
    } else if (type === 'quality_gate') {
      t.schema = [
        { key: 'verdict', type: 'enum', required: true, evidence: true },
        { key: 'basis', type: 'array', required: true, evidence: true },
        { key: 'narrative', type: 'string', required: false, evidence: false },
        { key: 'blockers', type: 'array', required: false, evidence: true },
      ];
      t.rules = ['P0 缺陷未关闭 → 阻断', '核心接口通过率 < 99% → 阻断', '安全高危发现 → 阻断'];
    }
    return t;
  }

  function hash(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return h; }

  /* ------------------------------------------------------------------
     3. 状态
     ------------------------------------------------------------------ */
  const S = {
    nodes: [], edges: [],
    sel: new Set(),
    selEdge: null,
    view: { x: 30, y: 40, scale: 0.82 },
    hist: [], fut: [],
    dirty: false,
    hideAux: false,
    clipboard: null,
    running: false,
    runLog: [],
    openExec: new Set(),
    nodeIdSeq: 1,
    edgeIdSeq: 1,
  };

  const $  = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));

  let viewport, world, edgeLayer, miniSvg;

  /* ------------------------------------------------------------------
     4. 初始化
     ------------------------------------------------------------------ */
  function init() {
    viewport = $('.canvas-viewport');
    world = $('.canvas-world');
    edgeLayer = $('#edge-layer');
    miniSvg = $('#mini-svg');

    loadGraph(DEFAULT_GRAPH);

    bindViewport();
    bindKeys();
    bindToolbar();
    buildPalette();
    bindMinimap();

    render();
    applyView();
    startAutosave();
    setSaveState('saved', '已保存 · 2 分钟前');

    const q = new URLSearchParams(location.search);
    if (q.get('wf')) {
      const wf = WORKFLOWS.find(w => w.id === q.get('wf'));
      if (wf) { S.name = wf.name; S.wfId = wf.id; renderTitle(); }
    }
  }

  function loadGraph(g) {
    S.nodes = g.nodes.map(n => Object.assign({ cfg: defaultCfg(n.type) }, n));
    S.edges = g.edges.map(e => Object.assign({}, e));
    S.sel.clear();
    S.nodeIdSeq = 100; S.edgeIdSeq = 100;
    S.name = g.name;
    S.wfId = g.wfId;
    S.status = g.status;
  }

  /* ------------------------------------------------------------------
     5. 渲染
     ------------------------------------------------------------------ */
  function render() {
    // 节点
    world.querySelectorAll('.wf-node').forEach(n => n.remove());
    S.nodes.forEach(n => {
      const el = document.createElement('div');
      el.className = 'wf-node' + (n.aux ? ' aux' : '') + (S.sel.has(n.id) ? ' selected' : '');
      el.dataset.id = n.id;
      el.style.left = n.x + 'px';
      el.style.top = n.y + 'px';
      el.innerHTML = nodeInner(n);
      world.appendChild(el);
    });

    // 连线
    edgeLayer.querySelectorAll('path.wf-edge, path.temp-edge, marker').forEach(n => n.remove());
    world.querySelectorAll('.edge-label').forEach(n => n.remove());
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML = `
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#4b5670"/>
      </marker>
      <marker id="arrow-sel" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#818cf8"/>
      </marker>
      <marker id="arrow-ok" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#10b981"/>
      </marker>`;
    edgeLayer.appendChild(defs);

    S.edges.forEach(e => {
      const a = nodeById(e.from), b = nodeById(e.to);
      if (!a || !b) return;
      const p = edgePath(a, b);
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', p.d);
      path.setAttribute('class', 'wf-edge' + (e.aux ? ' aux' : '') + (S.selEdge === e.id ? ' selected' : '') + (e.runState ? ' ' + e.runState : ''));
      path.setAttribute('marker-end', 'url(#' + (e.runState === 'active' ? 'arrow-ok' : S.selEdge === e.id ? 'arrow-sel' : 'arrow') + ')');
      path.dataset.id = e.id;
      edgeLayer.appendChild(path);

      if (e.label) {
        const lb = document.createElement('div');
        lb.className = 'edge-label' + (e.runState === 'active' ? ' active' : '');
        lb.dataset.eid = e.id;
        lb.textContent = e.label;
        lb.style.left = p.mx + 'px';
        lb.style.top = p.my + 'px';
        world.appendChild(lb);
      }
    });

    renderMinimap();
    updateCounts();
  }

  function nodeInner(n) {
    const meta = ALL_NODES[n.type] || { name: n.type, icon: '◻', cat: 'base' };
    const cm = CAT_META[meta.cat] || CAT_META.base;
    const c = n.cfg || {};
    const flags = [];
    if (c.async) flags.push('<span class="wf-flag async">异步</span>');
    if (c.resource) flags.push('<span class="wf-flag res">' + esc(c.resource) + '</span>');
    if (c.evidenceRequired) flags.push('<span class="wf-flag verify">证据必需</span>');
    const st = n.runState === 'done' ? 'ok' : n.runState === 'err' ? 'err' : n.runState === 'run' ? 'run' : '';
    return `
      <div class="wf-node-head">
        <span class="wf-node-ico" style="background:${cm.hex}22;color:${cm.hex}">${meta.icon || '◻'}</span>
        <span class="wf-node-title" title="${esc(c.name || meta.name)}">${esc(c.name || meta.name)}</span>
      </div>
      <div class="wf-node-body">
        <span class="st-dot ${st}"></span>
        <span class="mdl">${esc(c.model || '—')}</span>
        <span class="sp"></span>
        <span>${c.timeout || 120}s</span>
      </div>
      ${flags.length ? '<div class="wf-node-flags">' + flags.join('') + '</div>' : ''}
      <span class="wf-port port-in" data-port="in"></span>
      <span class="wf-port port-out" data-port="out"></span>`;
  }

  function nodeById(id) { return S.nodes.find(n => n.id === id); }

  function edgePath(a, b) {
    const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2;
    const x2 = b.x, y2 = b.y + NODE_H / 2;
    const dx = Math.max(38, Math.abs(x2 - x1) * 0.48);
    const d = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
    return { d, mx: (x1 + x2) / 2, my: (y1 + y2) / 2 };
  }

  function updateCounts() {
    const n = $('#stat-nodes'), e = $('#stat-edges');
    if (n) n.textContent = S.nodes.length;
    if (e) e.textContent = S.edges.length;
    const t = $('#top-title');
    if (t) t.textContent = S.name;
  }

  /* ------------------------------------------------------------------
     6. 视图变换
     ------------------------------------------------------------------ */
  function applyView() {
    const v = S.view;
    world.style.transform = `translate(${v.x}px, ${v.y}px) scale(${v.scale})`;
    const z = $('#zoom-val');
    if (z) z.textContent = Math.round(v.scale * 100) + '%';
    renderMinimap();
  }

  function zoomAt(cx, cy, factor) {
    const v = S.view;
    const ns = Math.min(2.2, Math.max(0.2, v.scale * factor));
    const px = (cx - v.x) / v.scale, py = (cy - v.y) / v.scale;
    v.scale = ns;
    v.x = cx - px * ns;
    v.y = cy - py * ns;
    applyView();
  }

  function screenToWorld(x, y) {
    const r = viewport.getBoundingClientRect();
    return { x: (x - r.left - S.view.x) / S.view.scale, y: (y - r.top - S.view.y) / S.view.scale };
  }

  /* ------------------------------------------------------------------
     7. 视口交互
     ------------------------------------------------------------------ */
  function bindViewport() {
    let panning = false, spaceDown = false, sx = 0, sy = 0, ox = 0, oy = 0;
    let dragging = null, dragOff = { x: 0, y: 0 }, moved = false, dragTarget = null;
    let connecting = null, marquee = null, mStart = null;

    viewport.addEventListener('mousedown', e => {
      const portEl = e.target.closest('.wf-port');
      const nodeEl = e.target.closest('.wf-node');
      const edgeEl = e.target.closest('path.wf-edge');

      // 1) 端口拖拽连线
      if (portEl) {
        e.preventDefault(); e.stopPropagation();
        if (portEl.dataset.port === 'out') {
          const nid = portEl.closest('.wf-node').dataset.id;
          connecting = { from: nid, path: null };
          viewport.classList.add('connecting');
          portEl.classList.add('armed');
        } else {
          // 输入端口：点击 = 选中目标节点
          const nid = portEl.closest('.wf-node').dataset.id;
          selectNode(nid, e.shiftKey);
          openConfig(nid);
        }
        return;
      }

      // 2) 边点击
      if (edgeEl) {
        e.stopPropagation();
        S.selEdge = edgeEl.dataset.id;
        S.sel.clear();
        render();
        toast('已选中连线，可按 Delete 删除', 'info');
        return;
      }

      // 3) 节点拖拽
      if (nodeEl && !spaceDown) {
        e.preventDefault();
        const nid = nodeEl.dataset.id;
        if (!S.sel.has(nid)) {
          if (!e.shiftKey) S.sel.clear();
          S.sel.add(nid);
        } else if (e.shiftKey) {
          S.sel.delete(nid);
        }
        render();
        if (!S.sel.has(nid)) return;
        dragging = { ids: Array.from(S.sel) };
        dragTarget = nid;
        const w = screenToWorld(e.clientX, e.clientY);
        const n = nodeById(nid);
        dragOff = { x: w.x - n.x, y: w.y - n.y };
        moved = false;
        nodeEl.classList.add('dragging');
        return;
      }

      // 4) 平移（空格 / 中键 / 右键拖）
      if (e.button === 1 || spaceDown || e.button === 2) {
        e.preventDefault();
        panning = true;
        sx = e.clientX; sy = e.clientY;
        ox = S.view.x; oy = S.view.y;
        viewport.classList.add('panning');
        return;
      }

      // 5) 框选
      if (e.button === 0) {
        if (!e.shiftKey) { S.sel.clear(); S.selEdge = null; render(); }
        const w = screenToWorld(e.clientX, e.clientY);
        marquee = { el: document.createElement('div'), x: w.x, y: w.y };
        marquee.el.className = 'marquee';
        world.appendChild(marquee.el);
        mStart = { cx: e.clientX, cy: e.clientY };
      }
    });

    window.addEventListener('mousemove', e => {
      // 连线中
      if (connecting) {
        const w = screenToWorld(e.clientX, e.clientY);
        const a = nodeById(connecting.from);
        const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2;
        const dx = Math.max(38, Math.abs(w.x - x1) * 0.48);
        const d = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${w.x - dx} ${w.y}, ${w.x} ${w.y}`;
        let tp = edgeLayer.querySelector('path.temp-edge');
        if (!tp) {
          tp = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          tp.setAttribute('class', 'temp-edge');
          edgeLayer.appendChild(tp);
        }
        tp.setAttribute('d', d);
        // 高亮可落点
        $$('.wf-port.port-in').forEach(p => p.classList.remove('target-ok'));
        const target = document.elementFromPoint(e.clientX, e.clientY);
        const p = target && target.closest && target.closest('.wf-port.port-in');
        if (p) p.classList.add('target-ok');
        return;
      }

      // 节点拖拽
      if (dragging) {
        const w = screenToWorld(e.clientX, e.clientY);
        dragging.ids.forEach(id => {
          const n = nodeById(id);
          if (!n) return;
          n.x = Math.round(w.x - dragOff.x);
          n.y = Math.round(w.y - dragOff.y);
        });
        moved = true;
        render();
        return;
      }

      // 平移
      if (panning) {
        S.view.x = ox + (e.clientX - sx);
        S.view.y = oy + (e.clientY - sy);
        applyView();
        return;
      }

      // 框选
      if (marquee) {
        const w = screenToWorld(e.clientX, e.clientY);
        const x = Math.min(w.x, marquee.x), y = Math.min(w.y, marquee.y);
        const bw = Math.abs(w.x - marquee.x), bh = Math.abs(w.y - marquee.y);
        marquee.el.style.left = x + 'px';
        marquee.el.style.top = y + 'px';
        marquee.el.style.width = bw + 'px';
        marquee.el.style.height = bh + 'px';
        // 选中范围内节点
        S.sel.clear();
        S.nodes.forEach(n => {
          if (n.x < x + bw && n.x + NODE_W > x && n.y < y + bh && n.y + NODE_H > y) S.sel.add(n.id);
        });
        render();
      }
    });

    window.addEventListener('mouseup', e => {
      if (connecting) {
        const target = document.elementFromPoint(e.clientX, e.clientY);
        const p = target && target.closest && target.closest('.wf-port.port-in');
        if (p) {
          const to = p.closest('.wf-node').dataset.id;
          addEdge(connecting.from, to);
        } else {
          const nd = target && target.closest && target.closest('.wf-node');
          if (nd && nd.dataset.id !== connecting.from) {
            // 松开在节点上 → 连到该节点
            addEdge(connecting.from, nd.dataset.id);
          }
        }
        $$('.wf-port').forEach(x => x.classList.remove('armed', 'target-ok'));
        const tp = edgeLayer.querySelector('path.temp-edge');
        tp && tp.remove();
        connecting = null;
        viewport.classList.remove('connecting');
      }
      if (dragging) {
        $$('.wf-node.dragging').forEach(x => x.classList.remove('dragging'));
        if (moved) { pushHistory(); markDirty(); }
        else if (dragTarget) { openConfig(dragTarget); }   /* 单击节点打开配置抽屉 */
        dragging = null; dragTarget = null;
      }
      if (marquee) { marquee.el.remove(); marquee = null; render(); }
      if (panning) { panning = false; viewport.classList.remove('panning'); }
    });

    // 滚轮缩放
    viewport.addEventListener('wheel', e => {
      e.preventDefault();
      const r = viewport.getBoundingClientRect();
      if (e.ctrlKey || e.metaKey || Math.abs(e.deltaY) > 0 && !e.shiftKey) {
        const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
        zoomAt(e.clientX - r.left, e.clientY - r.top, factor);
      } else {
        S.view.x -= e.deltaX; S.view.y -= e.deltaY;
        applyView();
      }
    }, { passive: false });

    // 空格光标
    window.addEventListener('keydown', e => {
      if (e.code === 'Space' && !isTyping(e)) {
        spaceDown = true;
        viewport.classList.add('space-ready');
        e.preventDefault();
      }
    });
    window.addEventListener('keyup', e => {
      if (e.code === 'Space') { spaceDown = false; viewport.classList.remove('space-ready'); }
    });
    viewport.addEventListener('contextmenu', e => e.preventDefault());
  }

  function isTyping(e) {
    const t = e.target.tagName;
    return t === 'INPUT' || t === 'TEXTAREA' || e.target.isContentEditable;
  }

  /* ------------------------------------------------------------------
     8. 选择 / 编辑
     ------------------------------------------------------------------ */
  function selectNode(id, add) {
    if (!add) S.sel.clear();
    S.sel.add(id);
    render();
  }

  function addEdge(from, to) {
    if (from === to) { toast('不能连接到自身', 'warn'); return; }
    if (S.edges.some(e => e.from === from && e.to === to)) { toast('连线已存在', 'warn'); return; }
    const a = nodeById(from), b = nodeById(to);
    if (!a || !b) return;
    // 数据契约校验（PRD §3.2）
    const check = contractCheck(a, b);
    if (check === 'mismatch') {
      toast('数据契约不匹配：' + (ALL_NODES[a.type]?.name) + ' → ' + (ALL_NODES[b.type]?.name) + ' 需人工映射', 'err');
      return;
    }
    const id = 'e' + (++S.edgeIdSeq);
    S.edges.push({ id, from, to, label: check === 'needs-map' ? '待映射' : '' });
    pushHistory(); markDirty(); render();
    toast('已连接：' + (ALL_NODES[a.type]?.name) + ' → ' + (ALL_NODES[b.type]?.name), 'ok');
  }

  function contractCheck(a, b) {
    const outs = a.cfg?.schema?.map(s => s.key) || [];
    const ins = b.cfg?.inputs?.map(i => i.from) || [];
    if (!ins.length) return 'ok';
    const unmatched = ins.filter(i => i !== '手动输入' && !outs.includes(i));
    if (unmatched.length) return 'mismatch';
    return 'ok';
  }

  function deleteSelection() {
    if (S.selEdge) {
      S.edges = S.edges.filter(e => e.id !== S.selEdge);
      S.selEdge = null;
      pushHistory(); markDirty(); render();
      toast('已删除连线', 'ok');
      return;
    }
    if (!S.sel.size) return;
    const ids = Array.from(S.sel);
    S.nodes = S.nodes.filter(n => !S.sel.has(n.id));
    S.edges = S.edges.filter(e => !ids.includes(e.from) && !ids.includes(e.to));
    S.sel.clear();
    pushHistory(); markDirty(); render();
    toast('已删除 ' + ids.length + ' 个节点', 'ok');
  }

  function copySelection() {
    const nodes = S.nodes.filter(n => S.sel.has(n.id));
    if (!nodes.length) return;
    S.clipboard = JSON.parse(JSON.stringify(nodes));
    toast('已复制 ' + nodes.length + ' 个节点', 'ok');
  }

  function pasteSelection() {
    if (!S.clipboard || !S.clipboard.length) return;
    const map = {};
    const clones = S.clipboard.map(n => {
      const id = 'n' + (++S.nodeIdSeq);
      map[n.id] = id;
      return Object.assign(JSON.parse(JSON.stringify(n)), { id, x: n.x + 30, y: n.y + 30 });
    });
    S.nodes = S.nodes.concat(clones);
    // 克隆内部连线
    S.clipboard.forEach(n => {
      (n._edges || []).forEach(e => {
        if (map[e.from] && map[e.to]) S.edges.push({ id: 'e' + (++S.edgeIdSeq), from: map[e.from], to: map[e.to], label: e.label });
      });
    });
    S.sel.clear();
    clones.forEach(c => S.sel.add(c.id));
    pushHistory(); markDirty(); render();
    toast('已粘贴 ' + clones.length + ' 个节点', 'ok');
  }

  /* ------------------------------------------------------------------
     9. 历史
     ------------------------------------------------------------------ */
  function snapshot() {
    return JSON.stringify({ nodes: S.nodes, edges: S.edges });
  }
  function pushHistory() {
    S.hist.push(snapshot());
    if (S.hist.length > 60) S.hist.shift();
    S.fut.length = 0;
  }
  function undo() {
    if (S.hist.length < 2) { toast('没有可撤销的操作', 'warn'); return; }
    S.fut.push(snapshot());
    const s = JSON.parse(S.hist.pop());
    S.nodes = s.nodes; S.edges = s.edges; S.sel.clear();
    render(); markDirty();
    toast('已撤销', 'ok');
  }
  function redo() {
    if (!S.fut.length) { toast('没有可重做的操作', 'warn'); return; }
    S.hist.push(snapshot());
    const s = JSON.parse(S.fut.pop());
    S.nodes = s.nodes; S.edges = s.edges; S.sel.clear();
    render(); markDirty();
    toast('已重做', 'ok');
  }

  /* ------------------------------------------------------------------
     10. 顶栏
     ------------------------------------------------------------------ */
  function bindToolbar() {
    $('#btn-undo')?.addEventListener('click', undo);
    $('#btn-redo')?.addEventListener('click', redo);
    $('#btn-save')?.addEventListener('click', () => {
      setSaveState('saving', '保存中…');
      setTimeout(() => { setSaveState('saved', '已保存 · 刚刚'); S.dirty = false; toast('工作流已保存（v12）', 'ok'); }, 700);
    });
    $('#btn-zoom-in')?.addEventListener('click', () => { const r = viewport.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, 1.2); });
    $('#btn-zoom-out')?.addEventListener('click', () => { const r = viewport.getBoundingClientRect(); zoomAt(r.width / 2, r.height / 2, 1 / 1.2); });
    $('#zoom-val')?.addEventListener('click', () => { S.view.scale = 0.82; S.view.x = 30; S.view.y = 40; applyView(); });
    $('#btn-fit')?.addEventListener('click', fitView);
    $('#btn-hide-aux')?.addEventListener('click', () => {
      S.hideAux = !S.hideAux;
      world.classList.toggle('aux-hidden', S.hideAux);
      $('#btn-hide-aux').classList.toggle('active', S.hideAux);
      toast(S.hideAux ? '已隐藏辅助节点，仅展示主流程' : '已显示全部节点', 'info');
    });
    $('#btn-validate')?.addEventListener('click', toggleValidate);
    $('#btn-run')?.addEventListener('click', startRun);
    $('#btn-history')?.addEventListener('click', showHistory);
    $('#btn-exit')?.addEventListener('click', () => location.href = 'workflows.html');
  }

  function renderTitle() {
    const t = $('#top-title');
    if (t) t.textContent = S.name;
  }

  function fitView() {
    if (!S.nodes.length) return;
    const xs = S.nodes.map(n => n.x), ys = S.nodes.map(n => n.y);
    const minX = Math.min(...xs) - 40, minY = Math.min(...ys) - 40;
    const maxX = Math.max(...xs) + NODE_W + 40, maxY = Math.max(...ys) + NODE_H + 40;
    const r = viewport.getBoundingClientRect();
    const sc = Math.min(r.width / (maxX - minX), r.height / (maxY - minY), 1.1);
    S.view.scale = sc;
    S.view.x = (r.width - (maxX - minX) * sc) / 2 - minX * sc;
    S.view.y = (r.height - (maxY - minY) * sc) / 2 - minY * sc;
    applyView();
    toast('已适配视图', 'info');
  }

  function setSaveState(cls, text) {
    const el = $('#save-state');
    if (!el) return;
    el.className = 'ed-save-state ' + cls;
    el.innerHTML = `<span class="dot"></span><span>${esc(text)}</span>`;
  }

  function markDirty() {
    S.dirty = true;
    setSaveState('saving', '有未保存更改');
  }

  function startAutosave() {
    setInterval(() => {
      if (!S.dirty) return;
      setSaveState('saving', '自动保存中…');
      setTimeout(() => { S.dirty = false; setSaveState('saved', '草稿已自动保存'); }, 600);
    }, 5000);
  }

  /* ------------------------------------------------------------------
     11. 左侧节点模板库
     ------------------------------------------------------------------ */
  function buildPalette() {
    const box = $('#lib-body');
    if (!box) return;
    Object.keys(NODE_CATALOG).forEach(cat => {
      const g = NODE_CATALOG[cat];
      const wrap = document.createElement('div');
      wrap.className = 'ed-cat';
      wrap.dataset.cat = cat;
      wrap.innerHTML = `
        <div class="ed-cat-head"><span class="ar">▼</span><span class="ed-cat-dot" style="background:${g.color}"></span><span>${esc(g.name)}</span><span class="count" style="margin-left:auto;font-size:10px;color:var(--tx-4)">${g.nodes.length}</span></div>
        <div class="ed-cat-body">${g.nodes.map(n => `
          <div class="ed-node-item" data-type="${n.id}" title="${esc(n.desc)}">
            <span class="ni">${n.icon}</span><span class="nt">${esc(n.name)}</span>
          </div>`).join('')}</div>`;
      box.appendChild(wrap);
      wrap.querySelector('.ed-cat-head').addEventListener('click', () => wrap.classList.toggle('collapsed'));
    });

    // 拖拽到画布
    box.querySelectorAll('.ed-node-item').forEach(item => {
      item.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', item.dataset.type);
        e.dataTransfer.effectAllowed = 'copy';
        item.classList.add('dragging');
        const ghost = document.createElement('div');
        ghost.className = 'drag-ghost';
        ghost.innerHTML = `<span>${item.querySelector('.ni').textContent}</span><span>${item.querySelector('.nt').textContent}</span>`;
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, 12, 12);
        setTimeout(() => ghost.remove(), 60);
      });
      item.addEventListener('dragend', () => item.classList.remove('dragging'));
      // 点击也可添加
      item.addEventListener('dblclick', () => addNodeAtCenter(item.dataset.type));
    });

    viewport.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; });
    viewport.addEventListener('drop', e => {
      e.preventDefault();
      const type = e.dataTransfer.getData('text/plain');
      if (!type) return;
      const w = screenToWorld(e.clientX, e.clientY);
      addNode(type, Math.round(w.x - NODE_W / 2), Math.round(w.y - NODE_H / 2));
    });

    // 搜索
    const ls = $('#lib-search');
    ls?.addEventListener('input', () => {
      const q = ls.value.trim().toLowerCase();
      $$('.ed-cat', box).forEach(cat => {
        let any = false;
        $$('.ed-node-item', cat).forEach(it => {
          const hit = !q || it.textContent.toLowerCase().includes(q);
          it.style.display = hit ? '' : 'none';
          if (hit) any = true;
        });
        cat.style.display = any ? '' : 'none';
      });
    });
  }

  function addNode(type, x, y) {
    const meta = ALL_NODES[type];
    if (!meta) return;
    const n = { id: 'n' + (++S.nodeIdSeq), type, x, y, cfg: defaultCfg(type) };
    S.nodes.push(n);
    S.sel.clear(); S.sel.add(n.id);
    pushHistory(); markDirty(); render();
    toast('已添加节点：' + meta.name, 'ok');
    openConfig(n.id);
    return n;
  }

  function addNodeAtCenter(type) {
    const r = viewport.getBoundingClientRect();
    const w = screenToWorld(r.left + r.width / 2, r.top + r.height / 2);
    return addNode(type, Math.round(w.x - NODE_W / 2), Math.round(w.y - NODE_H / 2));
  }

  /* ------------------------------------------------------------------
     12. 缩略图
     ------------------------------------------------------------------ */
  function bindMinimap() {
    if (!miniSvg) return;
    miniSvg.addEventListener('click', e => {
      const r = miniSvg.getBoundingClientRect();
      const mx = (e.clientX - r.left) / r.width, my = (e.clientY - r.top) / r.height;
      const bb = graphBounds();
      const w = bb.maxX - bb.minX, h = bb.maxY - bb.minY;
      const vr = viewport.getBoundingClientRect();
      const cx = bb.minX + mx * w - (vr.width / 2) / S.view.scale;
      const cy = bb.minY + my * h - (vr.height / 2) / S.view.scale;
      S.view.x = -cx * S.view.scale;
      S.view.y = -cy * S.view.scale;
      applyView();
    });
  }

  function graphBounds() {
    if (!S.nodes.length) return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
    const xs = S.nodes.map(n => n.x), ys = S.nodes.map(n => n.y);
    return {
      minX: Math.min(...xs) - 60, minY: Math.min(...ys) - 60,
      maxX: Math.max(...xs) + NODE_W + 60, maxY: Math.max(...ys) + NODE_H + 60,
    };
  }

  function renderMinimap() {
    if (!miniSvg) return;
    const bb = graphBounds();
    const W = 190, H = 124;
    const w = bb.maxX - bb.minX, h = bb.maxY - bb.minY;
    const sc = Math.min(W / w, H / h);
    const ox = (W - w * sc) / 2, oy = (H - h * sc) / 2;
    let s = '';
    S.nodes.forEach(n => {
      const meta = ALL_NODES[n.type] || {};
      s += `<rect class="mini-node cat-${meta.cat || 'base'}" x="${ox + (n.x - bb.minX) * sc}" y="${oy + (n.y - bb.minY) * sc}" width="${Math.max(3, NODE_W * sc)}" height="${Math.max(2, NODE_H * sc)}" rx="1.5"/>`;
    });
    // 视口矩形
    const vr = viewport ? viewport.getBoundingClientRect() : { width: 800, height: 600 };
    const vx = (-S.view.x) / S.view.scale, vy = (-S.view.y) / S.view.scale;
    const vw = vr.width / S.view.scale, vh = vr.height / S.view.scale;
    s += `<rect class="mini-view" x="${ox + (vx - bb.minX) * sc}" y="${oy + (vy - bb.minY) * sc}" width="${vw * sc}" height="${vh * sc}" rx="2"/>`;
    miniSvg.innerHTML = s;
  }

  /* ------------------------------------------------------------------
     13. 结构校验（PRD §7.2）
     ------------------------------------------------------------------ */
  function validate() {
    const issues = [];
    const incoming = id => S.edges.filter(e => e.to === id);
    const outgoing = id => S.edges.filter(e => e.from === id);
    const VERIFY_TYPES = ['triage', 'quality_gate', 'sufficiency', 'asset_certify', 'contract_check', 'db_consistency'];

    // 从某节点出发，下游可达的所有节点 id
    function downstream(id) {
      const seen = new Set(), stack = [id], out = new Set();
      while (stack.length) {
        const cur = stack.pop();
        outgoing(cur).forEach(e => {
          if (!seen.has(e.to)) { seen.add(e.to); out.add(e.to); stack.push(e.to); }
        });
      }
      return out;
    }

    S.nodes.forEach(n => {
      const meta = ALL_NODES[n.type] || {};
      const nm = meta.name || n.type;

      // 执行类节点必须存在可达的下游验证节点
      if (['api_test', 'ui_explore', 'browser_use', 'airtest', 'perf_test', 'security_scan', 'a11y_test', 'compat_test', 'chaos_test', 'visual_regression', 'unit_test_gen'].includes(n.type)) {
        const reach = downstream(n.id);
        const hasVerify = Array.from(reach).some(id => VERIFY_TYPES.includes(nodeById(id)?.type));
        if (!hasVerify) issues.push({ level: 'err', type: '缺少验证环节', desc: `执行类节点「${nm}」不存在可达的下游验证节点，失败结果无法闭环判定。`, node: n.id });
      }

      // 循环节点必须配置验收标准与最大迭代次数
      if (n.type === 'loop' && (!n.cfg.maxSteps || !n.cfg.acceptance)) {
        issues.push({ level: 'err', type: '循环节点配置不完整', desc: `「${nm}」必须配置验收标准与最大迭代次数，否则运行时无法确定终止条件。`, node: n.id });
      }

      // 计划确认门未通过 → 下游不可达（静态检查：门后须有可达的执行节点）
      if (n.type === 'plan_gate') {
        const down = outgoing(n.id);
        if (!down.length) issues.push({ level: 'err', type: '门禁悬空', desc: `「${nm}」后没有下游节点，执行节点不可达。`, node: n.id });
        else {
          const reach = downstream(n.id);
          const hasExec = Array.from(reach).some(id => (ALL_NODES[nodeById(id)?.type] || {}).cat === 'execute');
          if (!hasExec) issues.push({ level: 'err', type: '门禁后缺少执行节点', desc: `「${nm}」的下游没有可达的测试执行类节点，执行阶段不可达。`, node: n.id });
        }
      }

      // 异步任务提交必须配合汇聚等待节点
      if (n.type === 'async_task') {
        const hasJoin = outgoing(n.id).some(e => nodeById(e.to)?.type === 'join');
        if (!hasJoin) issues.push({ level: 'err', type: '可能阻塞', desc: `异步任务「${nm}」未配合汇聚等待节点，长任务可能阻塞无关分支。`, node: n.id });
      }

      // 缺陷归档必须是分诊确认缺陷后的唯一写入路径
      if (n.type === 'defect_archive') {
        const fromTriage = incoming(n.id).some(e => nodeById(e.from)?.type === 'triage');
        if (!fromTriage) issues.push({ level: 'err', type: '非法归档路径', desc: `「${nm}」必须由失败分诊确认缺陷后作为唯一写入路径。`, node: n.id });
      }

      // 工具白名单为空
      if (n.cfg && Array.isArray(n.cfg.tools) && n.cfg.tools.length === 0 && n.cat !== 'control') {
        issues.push({ level: 'warn', type: '工具白名单为空', desc: `「${nm}」未声明任何可调用工具，运行时将拒绝所有工具调用。`, node: n.id });
      }

      // 关键判定字段缺少证据引用
      if (n.cfg && n.cfg.evidenceRequired && Array.isArray(n.cfg.schema)) {
        const judged = n.cfg.schema.filter(s => s.required);
        if (judged.length && !judged.some(s => s.evidence)) {
          issues.push({ level: 'warn', type: '证据引用缺失', desc: `「${nm}」的必填判定字段（${judged.map(x => x.key).join('、')}）均未包含证据引用，平台将拒绝接受该输出。`, node: n.id });
        }
      }
    });

    // 数据契约
    S.edges.forEach(e => {
      const a = nodeById(e.from), b = nodeById(e.to);
      if (!a || !b) return;
      const outs = (a.cfg?.schema || []).map(s => s.key);
      const ins = (b.cfg?.inputs || []).map(i => i.from).filter(x => x && x !== '手动输入');
      const miss = ins.filter(x => !outs.includes(x));
      if (miss.length) {
        issues.push({ level: 'err', type: '数据契约不匹配', desc: `「${ALL_NODES[a.type]?.name}」→「${ALL_NODES[b.type]?.name}」的输入 ${miss.join('、')} 在上游输出 Schema 中不存在，需人工映射后才能连接。`, node: b.id, edge: e.id });
      }
    });

    // 开始/结束唯一性
    if (S.nodes.filter(n => n.type === 'start').length > 1) issues.push({ level: 'err', type: '入口冲突', desc: '工作流存在多个开始节点。', node: null });
    if (S.nodes.filter(n => n.type === 'end').length > 1) issues.push({ level: 'err', type: '出口冲突', desc: '工作流存在多个结束节点。', node: null });
    if (!S.nodes.some(n => n.type === 'start')) issues.push({ level: 'err', type: '缺少入口', desc: '工作流缺少开始节点。', node: null });
    if (!S.nodes.some(n => n.type === 'end')) issues.push({ level: 'err', type: '缺少出口', desc: '工作流缺少结束节点。', node: null });

    return issues;
  }

  function toggleValidate() {
    const p = $('#validate-panel');
    if (p.classList.contains('show')) { p.classList.remove('show'); return; }
    renderValidate();
    p.classList.add('show');
  }

  function renderValidate() {
    const issues = validate();
    const box = $('#validate-list');
    const errs = issues.filter(i => i.level === 'err').length;
    const warns = issues.length - errs;
    $('#validate-title').innerHTML = `结构校验 <span class="tag ${errs ? 'err' : 'ok'}" style="margin-left:auto">${errs} 阻断 · ${warns} 提示</span>`;
    if (!issues.length) {
      box.innerHTML = `<div class="empty" style="padding:26px 16px">
        <div class="ico" style="color:var(--ok-400);opacity:.7">✓</div>
        <h4>结构校验通过</h4>
        <p>未发现阻断性问题，可安全保存与运行。</p>
        <div class="notice info" style="text-align:left;margin-top:4px">
          <span class="ico">ⓘ</span>
          <div>试试删除「汇聚等待」节点，或从节点库添加一个「异步任务提交与轮询」节点且不连接汇聚节点——校验会立即拦截这两类结构问题。</div>
        </div></div>`;
      return;
    }
    box.innerHTML = issues.map((i, idx) => `
      <div class="validate-item" data-idx="${idx}">
        <span class="vi ${i.level}">${i.level === 'err' ? '✕' : '!'}</span>
        <div>
          <div class="vt">${esc(i.type)}</div>
          <div class="vd">${esc(i.desc)}</div>
          ${i.node ? `<div class="vloc">定位：${esc(ALL_NODES[nodeById(i.node)?.type]?.name || i.node)}</div>` : ''}
        </div>
      </div>`).join('');
    box.querySelectorAll('.validate-item').forEach(it => {
      it.addEventListener('click', () => {
        const issue = issues[+it.dataset.idx];
        if (!issue || !issue.node) return;
        const n = nodeById(issue.node);
        if (!n) return;
        S.sel.clear(); S.sel.add(n.id); render();
        centerOn(n.x, n.y);
        openConfig(n.id);
        $('#validate-panel').classList.remove('show');
      });
    });
  }

  function centerOn(x, y) {
    const r = viewport.getBoundingClientRect();
    S.view.x = r.width / 2 - (x + NODE_W / 2) * S.view.scale;
    S.view.y = r.height / 2 - (y + NODE_H / 2) * S.view.scale;
    applyView();
  }

  /* ------------------------------------------------------------------
     14. 历史版本
     ------------------------------------------------------------------ */
  function showHistory() {
    const versions = [
      { v: 'v12', t: '2026-10-20 16:38', by: '雪 樱', note: '安全探测节点加入范围限制', cur: true },
      { v: 'v11', t: '2026-10-19 20:10', by: '雪 樱', note: '质量门禁新增 P0 阻断规则' },
      { v: 'v10', t: '2026-10-18 09:44', by: '李 明', note: '增加自愈修复后重试分支' },
      { v: 'v9',  t: '2026-10-16 15:02', by: '王 强', note: '并行分发最大并发调整为 4' },
      { v: 'v8',  t: '2026-10-12 11:27', by: '李 明', note: '接入变异测试驱动质量信号' },
    ];
    openModal(`
      <div class="modal-head"><h3>版本历史</h3><span class="x" data-close>×</span></div>
      <div class="modal-body" style="padding:0">
        <div class="timeline" style="padding:18px 20px 6px">
          ${versions.map(v => `
            <div class="tl-item ${v.cur ? 'ok' : ''}">
              <div style="display:flex;align-items:center;gap:8px">
                <h5>${v.v} ${v.cur ? '<span class="tag brand">当前</span>' : ''}</h5>
                <span style="margin-left:auto;font-size:11px;color:var(--tx-3)">${v.t}</span>
              </div>
              <div class="meta">${esc(v.by)} · ${esc(v.note)}</div>
              ${v.cur ? '' : `<div style="margin-top:7px"><button class="btn xs" data-rollback="${v.v}">回滚到此版本</button></div>`}
            </div>`).join('')}
        </div>
      </div>
      <div class="modal-foot"><button class="btn" data-close>关闭</button></div>
    `, { size: 'wide', onClose: null }).el.addEventListener('click', e => {
      const rb = e.target.closest('[data-rollback]');
      if (rb) { toast('已回滚到 ' + rb.dataset.rollback + '，草稿已更新', 'ok'); }
    });
  }

  /* ------------------------------------------------------------------
     15. 试运行模拟
     ------------------------------------------------------------------ */
  function startRun() {
    if (S.running) { stopRun(); return; }
    const issues = validate();
    const errs = issues.filter(i => i.level === 'err');
    if (errs.length) {
      renderValidate();
      $('#validate-panel').classList.add('show');
      toast('存在 ' + errs.length + ' 项阻断性问题，请先修复后再运行', 'err');
      return;
    }
    S.running = true;
    S.runLog = [];
    S.openExec.clear();
    S.nodes.forEach(n => { n.runState = null; });
    S.edges.forEach(e => { e.runState = null; });

    const btn = $('#btn-run');
    btn.innerHTML = '<span class="spin"></span> 停止运行';
    btn.classList.add('danger');
    btn.classList.remove('primary');

    // 运行横幅
    const banner = document.createElement('div');
    banner.className = 'run-banner';
    banner.innerHTML = '<span class="pulse"></span><span id="run-msg">正在执行…</span><span class="tag brand" id="run-elapsed">0.0s</span>';
    viewport.appendChild(banner);
    S.banner = banner;

    // 拓扑排序 → 执行序列
    const order = topoOrder();
    openRunPanel(order);

    let i = 0;
    const t0 = performance.now();
    const tick = () => {
      if (!S.running) return;
      if (i >= order.length) { finishRun(); return; }
      const id = order[i];
      const n = nodeById(id);
      if (n) {
        n.runState = 'run';
        // 高亮入边
        S.edges.forEach(e => { if (e.to === id) e.runState = 'active'; });
        render();
        const msg = banner.querySelector('#run-msg');
        if (msg) msg.textContent = '正在执行：' + (n.cfg?.name || ALL_NODES[n.type]?.name);
        const el = banner.querySelector('#run-elapsed');
        if (el) el.textContent = ((performance.now() - t0) / 1000).toFixed(1) + 's';
        centerOn(n.x, n.y);
        addRunEntry(n, 'run');
      }
      const dur = 420 + Math.random() * 700;
      setTimeout(() => {
        if (!S.running) return;
        const nn = nodeById(id);
        const failChance = Math.random() < 0.10;
        if (nn) {
          nn.runState = failChance ? 'err' : 'done';
          addRunEntry(nn, failChance ? 'err' : 'done');
        }
        S.edges.forEach(e => { if (e.to === id) e.runState = failChance ? null : 'active'; });
        render();
        i++;
        tick();
      }, dur);
    };
    tick();
  }

  function topoOrder() {
    // 从开始节点做深度优先，保证 start 优先
    const start = S.nodes.find(n => n.type === 'start') || S.nodes[0];
    const out = new Map();
    S.nodes.forEach(n => out.set(n.id, []));
    S.edges.forEach(e => { if (out.has(e.from)) out.get(e.from).push(e.to); });
    const seen = new Set(), order = [];
    (function dfs(id) {
      if (seen.has(id)) return;
      seen.add(id);
      order.push(id);
      (out.get(id) || []).forEach(dfs);
    })(start.id);
    S.nodes.forEach(n => { if (!seen.has(n.id)) { order.push(n.id); seen.add(n.id); } });
    return order;
  }

  function stopRun() {
    S.running = false;
    const btn = $('#btn-run');
    btn.innerHTML = '▶ 执行';
    btn.classList.remove('danger');
    btn.classList.add('primary');
    if (S.banner) { S.banner.remove(); S.banner = null; }
    S.nodes.forEach(n => { if (n.runState === 'run') n.runState = null; });
    render();
    toast('运行已停止', 'warn');
  }

  function finishRun() {
    S.running = false;
    const btn = $('#btn-run');
    btn.innerHTML = '▶ 执行';
    btn.classList.remove('danger');
    btn.classList.add('primary');
    if (S.banner) {
      S.banner.querySelector('#run-msg').textContent = '运行完成 · 质量门禁裁决：有条件通过';
      setTimeout(() => { if (S.banner) { S.banner.remove(); S.banner = null; } }, 2600);
    }
    render();
    updateRunPanel();
    toast('运行完成，用时 6.2s，Token 消耗 18,402', 'ok');
  }

  function addRunEntry(n, state) {
    const meta = ALL_NODES[n.type] || {};
    const entry = {
      id: n.id, name: n.cfg?.name || meta.name, type: n.type, cat: meta.cat,
      state, cost: (Math.random() * 0.18 + 0.02), tokens: Math.floor(Math.random() * 4000 + 800),
      dur: (Math.random() * 2.4 + 0.3).toFixed(2) + 's',
      input: n.cfg?.userPrompt || '（继承上游输出）',
      output: buildOutput(n),
      tools: buildTools(n),
      evidence: n.cfg?.evidenceRequired ? ['日志片段 #' + Math.floor(Math.random() * 9000 + 1000), '请求响应 采样 #' + (200 + Math.floor(Math.random() * 700))] : [],
    };
    const existing = S.runLog.find(e => e.id === n.id);
    if (existing) Object.assign(existing, entry);   /* 同一节点只保留一条记录 */
    else S.runLog.push(entry);
    updateRunPanel();   /* 运行过程中实时刷新执行面板 */
  }

  function buildOutput(n) {
    const sch = n.cfg?.schema || [];
    const t = n.type;
    if (t === 'risk_rating') return '{\n  "risk_level": "P1",\n  "risk_score": 72,\n  "rationale": "影响 6 个模块，其中支付链路 2 个，历史缺陷密度高"\n}';
    if (t === 'quality_gate') return '{\n  "verdict": "有条件通过",\n  "basis": ["API 通过率 98.2%", "无高危安全问题", "性能 P99 达标"],\n  "blockers": ["UI 探索发现 2 个 P2 缺陷待确认"]\n}';
    if (t === 'impact_analysis') return '{\n  "affected_modules": ["order-core", "pay-gateway", "cart-service"],\n  "direct_risk": ["pay-gateway"],\n  "regression_scope": "订单 + 支付链路全量"\n}';
    if (t === 'triage') return '{\n  "classification": "测试缺陷",\n  "confidence": 0.86,\n  "routing": "self_heal"\n}';
    return '{\n' + sch.slice(0, 4).map(s => `  "${s.key}": ${s.type === 'number' ? 0 : s.type === 'array' ? '[]' : s.type === 'object' ? '{}' : '"…"'}`).join(',\n') + '\n}';
  }

  function buildTools(n) {
    const list = n.cfg?.tools || [];
    if (!list.length) return [];
    return list.map((t, i) => ({
      name: t,
      req: '{\n  "target": "' + (n.cfg?.name || 'target') + '",\n  "timeout": 30000\n}',
      res: '{\n  "status": ' + (i === 1 && Math.random() < 0.3 ? '"error"' : '"ok"') + ',\n  "latency_ms": ' + Math.floor(Math.random() * 800 + 40) + ',\n  "items": ' + Math.floor(Math.random() * 40) + '\n}',
      denied: i === 1 && Math.random() < 0.25,
    }));
  }

  /* ------------------------------------------------------------------
     16. 抽屉：节点配置 / 运行面板
     ------------------------------------------------------------------ */
  let drawer = null;
  function openConfig(nodeId) {
    const n = nodeById(nodeId);
    if (!n) return;
    if (drawer) { drawer.close(); drawer = null; }
    drawer = openDrawer('<div class="cfg-head" id="cfg-head"></div><div class="cfg-tabs tabs" id="cfg-tabs"></div><div class="cfg-body" id="cfg-body"></div><div class="cfg-foot" id="cfg-foot"></div>', {
      onClose: () => { drawer = null; }
    });
    renderConfig(n);
  }

  function renderConfig(n) {
    const meta = ALL_NODES[n.type] || {};
    const cm = CAT_META[meta.cat] || CAT_META.base;
    const head = $('#cfg-head');
    if (!head) return;
    head.innerHTML = `
      <div class="r1">
        <div class="ic" style="background:${cm.hex}22;color:${cm.hex}">${meta.icon || '◻'}</div>
        <div style="min-width:0;flex:1">
          <h3>${esc(n.cfg?.name || meta.name)}</h3>
          <div class="cat">${esc(cm.name)} · <span class="mono">${esc(n.id)}</span></div>
        </div>
        <button class="btn ghost icon sm" id="cfg-close" title="关闭">×</button>
      </div>
      <div class="row2">
        <button class="btn sm" id="cfg-debug">▶ 单节点调试</button>
        <button class="btn sm" id="cfg-dupe">复制节点</button>
        <button class="btn sm" id="cfg-del" style="margin-left:auto;color:var(--err-400)">删除</button>
      </div>`;

    const tabs = [
      ['basic', '基础信息'], ['model', '模型'], ['prompt', '提示词'], ['inputs', '输入绑定'],
      ['schema', '输出 Schema'], ['tools', '工具白名单'], ['skills', '能力包'],
      ['limits', '约束配置'], ['rules', '规则绑定'], ['async', '异步与资源'],
    ];
    $('#cfg-tabs').innerHTML = tabs.map((t, i) => `<div class="tab ${i === 0 ? 'active' : ''}" data-tab="${t[0]}">${t[1]}</div>`).join('');
    $$('#cfg-tabs .tab').forEach(t => t.addEventListener('click', () => {
      $$('#cfg-tabs .tab').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      renderCfgTab(n, t.dataset.tab);
    }));

    $('#cfg-foot').innerHTML = `
      <button class="btn" id="cfg-validate">结构校验</button>
      <button class="btn primary" id="cfg-apply" style="margin-left:auto">应用并关闭</button>`;

    $('#cfg-close').addEventListener('click', () => drawer && drawer.close());
    $('#cfg-apply').addEventListener('click', () => {
      pushHistory(); markDirty(); render();
      toast('节点配置已应用', 'ok');
      drawer && drawer.close();
    });
    $('#cfg-del').addEventListener('click', () => {
      S.sel.clear(); S.sel.add(n.id); deleteSelection();
      drawer && drawer.close();
    });
    $('#cfg-dupe').addEventListener('click', () => {
      const c = JSON.parse(JSON.stringify(n));
      c.id = 'n' + (++S.nodeIdSeq); c.x += 30; c.y += 30;
      S.nodes.push(c); pushHistory(); markDirty(); render();
      toast('已复制节点', 'ok'); openConfig(c.id);
    });
    $('#cfg-debug').addEventListener('click', () => debugNode(n));
    $('#cfg-validate').addEventListener('click', () => {
      renderValidate();
      const p = $('#validate-panel');
      if (p) { p.classList.add('show'); }
    });

    renderCfgTab(n, 'basic');
  }

  function renderCfgTab(n, tab) {
    const box = $('#cfg-body');
    if (!box) return;
    const c = n.cfg;
    const meta = ALL_NODES[n.type] || {};
    const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

    if (tab === 'basic') {
      box.innerHTML = `
        <div class="field">
          <label>节点名称 <span class="req">*</span></label>
          <input class="input" id="f-name" value="${esc(c.name)}">
        </div>
        <div class="field">
          <label>节点描述</label>
          <textarea class="textarea" id="f-desc">${esc(c.desc)}</textarea>
          <div class="hint">${esc(meta.desc || '')}</div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>节点分类</label>
            <input class="input" value="${esc((CAT_META[meta.cat] || {}).name || '')}" disabled>
          </div>
          <div class="field">
            <label>节点图标</label>
            <input class="input" value="${esc(c.icon || meta.icon || '')}">
          </div>
        </div>
        <div class="field">
          <label>继承策略</label>
          <select class="select">
            <option>继承平台级规则 + 使用全站默认模型</option>
            <option>继承平台级规则 + 使用个人级模型配置</option>
            <option>仅使用节点级完全自定义配置</option>
          </select>
          <div class="hint">节点可独立替换模型，不影响工作流拓扑与数据契约。</div>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>执行日志</label>
          <div class="notice info">
            <span class="ico">ⓘ</span>
            <div>该节点独立记录输入、推理摘要、工具调用、输出、耗时与成本。
            <a href="runs.html" target="_blank">查看最近一次执行日志 →</a></div>
          </div>
        </div>`;
      $('#f-name').addEventListener('input', e => { c.name = e.target.value; markDirty(); render(); });
      $('#f-desc').addEventListener('input', e => { c.desc = e.target.value; markDirty(); });
    }

    else if (tab === 'model') {
      box.innerHTML = `
        <div class="field">
          <label>模型 <span class="req">*</span></label>
          <select class="select" id="f-model">
            ${MODEL_POOL.map(m => `<option ${m === c.model ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
          <div class="hint">来源：全站默认配置。可在「模型与额度」中调整个人级绑定。</div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>Temperature</label>
            <input class="input" type="number" step="0.1" min="0" max="2" value="${c.temperature}">
          </div>
          <div class="field">
            <label>Top-P</label>
            <input class="input" type="number" step="0.05" min="0" max="1" value="${c.topP}">
          </div>
        </div>
        <div class="field">
          <label>最大步数</label>
          <input class="input" type="number" value="${c.maxSteps}">
          <div class="hint">单节点最多推理步数，超出由平台代码强制终止。</div>
        </div>
        <div class="field">
          <label>连接测试</label>
          <button class="btn" id="f-conntest">测试模型连通性</button>
          <div class="hint">确保配置可用后再投入工作流。</div>
        </div>`;
      $('#f-model').addEventListener('change', e => { c.model = e.target.value; markDirty(); render(); });
      $('#f-conntest').addEventListener('click', e => {
        const b = e.target; b.disabled = true; b.innerHTML = '<span class="spin"></span> 测试中…';
        setTimeout(() => { b.disabled = false; b.textContent = '测试模型连通性'; toast('连接成功 · 延迟 218ms', 'ok'); }, 1200);
      });
    }

    else if (tab === 'prompt') {
      box.innerHTML = `
        <div class="field">
          <label>System Prompt</label>
          <textarea class="textarea" id="f-sys" style="min-height:110px">${esc(c.systemPrompt || '你是测试领域专家智能体，负责……')}</textarea>
        </div>
        <div class="field">
          <label>User Prompt</label>
          <textarea class="textarea" id="f-user" style="min-height:110px">${esc(c.userPrompt || '请基于以下输入完成测试任务：\n{{$input}}')}</textarea>
          <div class="hint">支持使用 <span class="mono" style="color:var(--brand-400)">{{$变量}}</span> 引用上游节点输出，插入变量可在下方输入绑定中查看。</div>
        </div>
        <div class="field">
          <label>可用变量</label>
          <div style="display:flex;flex-wrap:wrap;gap:5px">
            ${(c.inputs || []).map(i => `<span class="tool-chip">${esc(i.key)}<span class="x" style="cursor:pointer" data-ins="${esc(i.key)}">⊕</span></span>`).join('') || '<span style="color:var(--tx-4);font-size:11.5px">未绑定变量</span>'}
          </div>
        </div>
        <div class="field">
          <label>推理策略</label>
          <select class="select">
            <option>逐步推理（默认）</option>
            <option>先规划后执行</option>
            <option>直接执行</option>
            <option>结构化输出优先</option>
          </select>
          <div class="hint">规划、执行、验证三者在平台中由不同节点承担，单节点不混合职责。</div>
        </div>`;
      box.querySelectorAll('[data-ins]').forEach(b => b.addEventListener('click', () => {
        const ta = $('#f-user');
        ta.value = (ta.value || '') + ' {{$' + b.dataset.ins + '}}';
        toast('已插入变量 ' + b.dataset.ins, 'info');
      }));
      $('#f-sys').addEventListener('input', e => { c.systemPrompt = e.target.value; markDirty(); });
      $('#f-user').addEventListener('input', e => { c.userPrompt = e.target.value; markDirty(); });
    }

    else if (tab === 'inputs') {
      const upstream = S.edges.filter(e => e.to === n.id).map(e => nodeById(e.from)).filter(Boolean);
      box.innerHTML = `
        <div class="field">
          <label>上游节点</label>
          <div class="notice ${upstream.length ? 'info' : 'warn'}">
            <span class="ico">${upstream.length ? '⇢' : '!'}</span>
            <div>${upstream.length
              ? '检测到 ' + upstream.length + ' 个上游节点：' + upstream.map(u => esc(u.cfg?.name || ALL_NODES[u.type]?.name)).join('、')
              : '该节点暂无上游输入，请先在画布中连接输入端口。'}</div>
          </div>
        </div>
        ${(c.inputs || []).map((i, idx) => `
          <div class="var-row">
            <span class="vn">${esc(i.key)}</span>
            <span class="vv">${esc(i.from)} · ${esc(i.type || 'string')}</span>
            <span class="tag ${i.mapped ? 'ok' : 'warn'}" style="margin-left:auto">${i.mapped ? '已映射' : '待映射'}</span>
            <span class="vx" data-del-input="${idx}">✕</span>
          </div>`).join('') || '<div style="color:var(--tx-4);font-size:11.5px;padding:8px 0">未定义输入变量</div>'}
        <div class="field" style="margin-top:10px">
          <button class="btn sm" id="f-add-input">+ 添加输入变量</button>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>数据契约校验</label>
          <select class="select">
            <option>严格模式：不匹配时阻止连线</option>
            <option>宽松模式：标记为待人工映射</option>
          </select>
          <div class="hint">上游输出 Schema 与下游输入要求不匹配时给出明确提示，阻止非法连接或标记为待人工映射。</div>
        </div>`;
      box.querySelectorAll('[data-del-input]').forEach(b => b.addEventListener('click', () => {
        c.inputs.splice(+b.dataset.delInput, 1); renderCfgTab(n, 'inputs');
      }));
      $('#f-add-input').addEventListener('click', () => {
        c.inputs.push({ key: 'new_var', from: '手动输入', type: 'string', mapped: false });
        renderCfgTab(n, 'inputs');
      });
    }

    else if (tab === 'schema') {
      box.innerHTML = `
        <div class="notice ok" style="margin-bottom:12px">
          <span class="ico">✓</span>
          <div>输出禁止自由文本黑箱输出。关键判定字段必须包含<b>证据引用</b>，证据存在性由平台代码校验，不接受模型自我声明。</div>
        </div>
        ${(c.schema || []).map(s => `
          <div class="schema-row">
            <span class="k">${esc(s.key)}</span>
            <span class="ty">${esc(s.type)}</span>
            ${s.required ? '<span class="req">必填</span>' : ''}
            ${s.evidence ? '<span class="ev">证据引用 ✓</span>' : '<span class="req" style="margin-left:auto">缺证据</span>'}
          </div>`).join('')}
        <div class="field" style="margin-top:12px">
          <button class="btn sm" id="f-add-field">+ 添加输出字段</button>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>结构化输出模式</label>
          <select class="select"><option>严格 JSON Schema</option><option>结构化对象 + 自由文本补充</option></select>
        </div>`;
      $('#f-add-field').addEventListener('click', () => {
        c.schema.push({ key: 'new_field', type: 'string', required: false, evidence: false });
        renderCfgTab(n, 'schema');
      });
    }

    else if (tab === 'tools') {
      const allTools = ['http.client', 'browser.driver', 'vision.ocr', 'device.control', 'perf.runner', 'log.search', 'trace.query', 'repo.diff', 'patch.apply', 'rule.engine', 'report.render', 'defect.tracker.write', 'kb.retrieve', 'workflow.runtime', 'expr.evaluate', 'mcp.invoke', 'sandbox.exec', 'data.factory'];
      box.innerHTML = `
        <div class="notice warn" style="margin-bottom:12px">
          <span class="ico">!</span>
          <div>工具白名单外的调用在<b>运行时被拒绝</b>并记录审计事件，节点级隔离不可绕过。</div>
        </div>
        <div class="field">
          <label>已授权工具 <span class="req">*</span></label>
          <div>${(c.tools || []).map(t => `<span class="tool-chip">${esc(t)}<span class="x" data-del-tool="${esc(t)}">✕</span></span>`).join('') || '<span style="color:var(--tx-4);font-size:11.5px">尚未授权任何工具</span>'}</div>
        </div>
        <div class="field">
          <label>添加工具</label>
          <select class="select" id="f-add-tool">${allTools.map(t => `<option>${t}</option>`).join('')}</select>
          <div class="field" style="margin-top:8px"><button class="btn sm" id="f-do-add-tool">+ 授权</button></div>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>显式拒绝（运行时拦截并告警）</label>
          <div>${(c.deniedTools || []).map(t => `<span class="tool-chip deny">${esc(t)}<span class="x" data-undeny="${esc(t)}">✕</span></span>`).join('')}</div>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>白名单判定记录</label>
          <div class="notice info"><span class="ico">ⓘ</span><div>每次白名单判定结果写入执行追踪与证据账本，可在「审计账本」中按节点查询。</div></div>
        </div>`;
      box.querySelectorAll('[data-del-tool]').forEach(b => b.addEventListener('click', () => {
        c.tools = c.tools.filter(t => t !== b.dataset.delTool); renderCfgTab(n, 'tools');
      }));
      box.querySelectorAll('[data-undeny]').forEach(b => b.addEventListener('click', () => {
        c.deniedTools = c.deniedTools.filter(t => t !== b.dataset.undeny); renderCfgTab(n, 'tools');
      }));
      $('#f-do-add-tool').addEventListener('click', () => {
        const v = $('#f-add-tool').value;
        if (!c.tools.includes(v)) { c.tools.push(v); markDirty(); renderCfgTab(n, 'tools'); toast('已授权工具 ' + v, 'ok'); }
      });
    }

    else if (tab === 'skills') {
      const skills = [
        { id: 'sk_auth', name: '通用鉴权与权限校验能力包', ver: 'v4.0', cat: '认证' },
        { id: 'sk_data', name: '测试数据构造工具集', ver: 'v1.8', cat: '通用' },
        { id: 'sk_report', name: '标准报告模板包', ver: 'v2.1', cat: '报告' },
        { id: 'sk_locator', name: '智能定位器增强包', ver: 'v3.0', cat: 'UI' },
      ];
      box.innerHTML = `
        <div class="field">
          <label>已挂载能力包</label>
          ${(c.skills || []).map(s => `<div class="var-row"><span class="vn">${esc(s.name)}</span><span class="vv">${esc(s.ver)} · 版本已锁定</span><span class="vx" data-del-sk="${esc(s.id)}">✕</span></div>`).join('') || '<div style="color:var(--tx-4);font-size:11.5px;padding:6px 0">未挂载能力包</div>'}
        </div>
        <div class="field">
          <label>可挂载能力包</label>
          ${skills.filter(s => !(c.skills || []).some(x => x.id === s.id)).map(s => `
            <div class="var-row">
              <span class="vn">${esc(s.name)}</span>
              <span class="vv">${esc(s.ver)} · ${esc(s.cat)}</span>
              <button class="btn xs" style="margin-left:auto" data-add-sk="${s.id}">挂载</button>
            </div>`).join('')}
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>版本锁定</label>
          <div class="notice info"><span class="ico">ⓘ</span><div>挂载时锁定版本号，工作流版本快照可回溯，升级需通过副作用回归检查。</div></div>
        </div>`;
      box.querySelectorAll('[data-add-sk]').forEach(b => b.addEventListener('click', () => {
        const s = skills.find(x => x.id === b.dataset.addSk);
        c.skills.push({ id: s.id, name: s.name, ver: s.ver });
        markDirty(); renderCfgTab(n, 'skills'); toast('已挂载 ' + s.name, 'ok');
      }));
      box.querySelectorAll('[data-del-sk]').forEach(b => b.addEventListener('click', () => {
        c.skills = c.skills.filter(x => x.id !== b.dataset.delSk); renderCfgTab(n, 'skills');
      }));
    }

    else if (tab === 'limits') {
      box.innerHTML = `
        <div class="field-row">
          <div class="field">
            <label>最大执行步数</label>
            <input class="input" type="number" value="${c.maxSteps}">
          </div>
          <div class="field">
            <label>超时时间（秒）</label>
            <input class="input" type="number" value="${c.timeout}">
          </div>
        </div>
        <div class="field">
          <label>Token 预算</label>
          <input class="input" type="number" value="${c.tokenBudget}">
          <div class="hint">超出预算按平台策略终止（硬停止 / 降级输出 / 升级人工），<b>不交由模型判断</b>。</div>
        </div>
        <div class="field-row">
          <div class="field">
            <label>重试次数</label>
            <input class="input" type="number" value="${c.retry}">
          </div>
          <div class="field">
            <label>退避策略</label>
            <select class="select">
              <option ${c.backoff === 'exponential' ? 'selected' : ''}>exponential</option>
              <option ${c.backoff === 'linear' ? 'selected' : ''}>linear</option>
              <option ${c.backoff === 'fixed' ? 'selected' : ''}>fixed</option>
            </select>
          </div>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>预算超限策略</label>
          <select class="select"><option>硬停止</option><option>降级输出</option><option>升级人工处理</option></select>
        </div>
        <div class="field">
          <label>重试消耗</label>
          <div class="notice info"><span class="ico">ⓘ</span><div>重试消耗纳入预算计量，可在成本报表中单独查看。</div></div>
        </div>`;
    }

    else if (tab === 'rules') {
      box.innerHTML = `
        <div class="field">
          <label>继承的平台级规则</label>
          <div class="notice info"><span class="ico">ⓘ</span><div>平台级规则（安全红线、证据校验、判定确定性）自动继承，<b>不可被节点配置覆盖</b>。</div></div>
        </div>
        <div class="field">
          <label>节点级附加规则</label>
          ${(c.rules || []).map((r, i) => `<div class="var-row"><span class="vn">规则 ${i + 1}</span><span class="vv">${esc(r)}</span><span class="vx" data-del-rule="${i}">✕</span></div>`).join('') || '<div style="color:var(--tx-4);font-size:11.5px;padding:6px 0">暂无附加规则</div>'}
        </div>
        <div class="field">
          <button class="btn sm" id="f-add-rule">+ 添加规则</button>
        </div>
        <div class="hr"></div>
        <div class="field">
          <label>规则评测</label>
          <div class="notice warn"><span class="ico">!</span><div>输出质量审计对生成类节点的输出做一致性、可追溯性与幻觉检测，评估结果可路由至人工复核或触发降级。</div></div>
        </div>`;
      box.querySelectorAll('[data-del-rule]').forEach(b => b.addEventListener('click', () => {
        c.rules.splice(+b.dataset.delRule, 1); renderCfgTab(n, 'rules');
      }));
      $('#f-add-rule').addEventListener('click', () => {
        c.rules.push('新增规则：输出必须附带证据引用，缺失则拒绝该输出');
        renderCfgTab(n, 'rules');
      });
    }

    else if (tab === 'async') {
      box.innerHTML = `
        <div class="field">
          <label>异步模式</label>
          <div class="segmented" id="f-async">
            <button class="${!c.async ? 'active' : ''}" data-v="0">同步执行</button>
            <button class="${c.async ? 'active' : ''}" data-v="1">异步提交</button>
          </div>
          <div class="hint">异步节点提交任务后立即返回任务标识与结果获取引用，需配合「汇聚等待」节点使用。</div>
        </div>
        ${c.async ? `
        <div class="field">
          <label>结果获取模式</label>
          <select class="select"><option>轮询（间隔 30s）</option><option>事件回调</option></select>
        </div>
        <div class="field">
          <label>最大执行时长</label>
          <input class="input" type="number" value="3600">
          <div class="hint">超时后按策略终止或转人工处理。</div>
        </div>` : ''}
        <div class="hr"></div>
        <div class="field">
          <label>资源需求声明</label>
          <input class="input" id="f-res" value="${esc(c.resource || '')}" placeholder="如：设备池 · 独占锁">
        </div>
        <div class="field">
          <label>资源数量</label>
          <input class="input" type="number" value="${c.resourceCount || 1}">
        </div>
        <div class="field">
          <label>锁策略</label>
          <select class="select"><option>互斥锁</option><option>共享锁</option><option>带超时的自动释放</option></select>
          <div class="hint">资源被占用时节点进入等待或按策略失败，工作流提供超时与降级分支。<a href="resources.html" target="_blank">查看资源池 →</a></div>
        </div>`;
      $$('#f-async button').forEach(b => b.addEventListener('click', () => {
        c.async = b.dataset.v === '1'; markDirty(); render(); renderCfgTab(n, 'async');
      }));
      const r = $('#f-res');
      if (r) r.addEventListener('input', e => { c.resource = e.target.value; markDirty(); render(); });
    }
  }

  /* ------------------------------------------------------------------
     17. 运行面板
     ------------------------------------------------------------------ */
  function openRunPanel(order) {
    if (drawer) { drawer.close(); drawer = null; }
    drawer = openDrawer('<div class="run-panel" id="run-panel"></div>', { onClose: () => { drawer = null; } });
    updateRunPanel();
  }

  function updateRunPanel() {
    const box = $('#run-panel');
    if (!box) return;
    const total = S.runLog.length;
    const done = S.runLog.filter(e => e.state === 'done').length;
    const errs = S.runLog.filter(e => e.state === 'err').length;
    const cost = S.runLog.reduce((a, b) => a + b.cost, 0);
    const tokens = S.runLog.reduce((a, b) => a + b.tokens, 0);
    const elapsed = S.runLog.reduce((a, b) => a + parseFloat(b.dur), 0);

    box.innerHTML = `
      <div class="run-head">
        <div style="display:flex;align-items:center;gap:8px">
          <h3 style="margin:0;font-size:14px">试运行 · ${esc(S.name)}</h3>
          <span class="tag brand" style="margin-left:auto">v12</span>
        </div>
        <div class="run-stat" style="margin-top:11px">
          <div class="s"><div class="k">已执行</div><div class="v">${done}/${total || 0}</div></div>
          <div class="s"><div class="k">失败</div><div class="v" style="color:${errs ? 'var(--err-400)' : 'inherit'}">${errs}</div></div>
          <div class="s"><div class="k">累计耗时</div><div class="v">${elapsed.toFixed(1)}s</div></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:10px;font-size:11px;color:var(--tx-3)">
          <span>Token <b class="mono" style="color:var(--tx-1)">${num(tokens)}</b></span>
          <span>成本 <b class="mono" style="color:var(--tx-1)">${money(cost)}</b></span>
          <span style="margin-left:auto"><a href="runs.html" target="_blank">完整追踪 →</a></span>
        </div>
      </div>
      <div class="run-body">
        <div class="exec-sec">
          <div class="lbl">质量门禁裁决 <span class="e">确定性规则引擎</span></div>
          <div class="gate-verdict cond">
            <div class="v">有条件通过</div>
            <div class="s">硬门禁 · 由平台规则引擎计算，模型不得覆盖判定结论</div>
            <div class="b">依据：API 通过率 98.2% · 无高危安全问题 · 性能 P99 达标 · UI 探索发现 2 个 P2 缺陷待确认</div>
          </div>
        </div>
        <div class="exec-sec">
          <div class="lbl">节点执行明细 <span class="e">按时间顺序</span></div>
          ${S.runLog.map((e, i) => `
            <div class="exec-node ${e.state === 'err' ? 'err' : e.state === 'run' ? 'run' : 'ok'}" data-i="${i}">
              <div class="en-head">
                <span class="st-dot ${e.state === 'err' ? 'err' : e.state === 'run' ? 'run' : 'ok'}" style="width:6px;height:6px;border-radius:50%;display:inline-block;background:${e.state === 'err' ? 'var(--err-500)' : e.state === 'run' ? 'var(--brand-400)' : 'var(--ok-500)'}"></span>
                <span class="t">${esc(e.name)}</span>
                <span class="d">${e.dur} · ${num(e.tokens)} tok · ${money(e.cost)}</span>
              </div>
              <div class="en-body">
                <div class="exec-sec">
                  <div class="lbl">输入</div>
                  <div class="code">${esc(e.input)}</div>
                </div>
                <div class="exec-sec">
                  <div class="lbl">输出</div>
                  <div class="code">${esc(e.output)}</div>
                </div>
                ${e.tools.length ? `
                <div class="exec-sec">
                  <div class="lbl">工具调用</div>
                  ${e.tools.map(t => `
                    <div class="tool-call ${t.denied ? 'denied' : ''}">
                      <div class="tc-h"><span class="nm">${esc(t.name)}</span><span class="rt">${t.denied ? '白名单拒绝' : 'OK'}</span></div>
                      <div class="tc-b">
                        <div class="code" style="margin-bottom:6px">${esc(t.req)}</div>
                        <div class="code">${esc(t.res)}</div>
                      </div>
                    </div>`).join('')}
                </div>` : ''}
                ${e.evidence.length ? `
                <div class="exec-sec">
                  <div class="lbl">证据引用 <span class="e">平台已校验存在性</span></div>
                  ${e.evidence.map(v => `<div class="var-row"><span class="vv">${esc(v)}</span><span class="tag ok" style="margin-left:auto">可追溯</span></div>`).join('')}
                </div>` : ''}
                <div style="display:flex;gap:6px;margin-top:8px">
                  <a class="btn xs" href="runs.html" target="_blank">查看完整追踪</a>
                  <a class="btn xs" href="audit.html" target="_blank">证据账本</a>
                </div>
              </div>
            </div>`).join('') || '<div style="color:var(--tx-4);font-size:11.5px">等待执行…</div>'}
        </div>
      </div>`;

    box.querySelectorAll('.exec-node .en-head').forEach(h => {
      h.addEventListener('click', () => {
        const card = h.parentElement;
        const i = +card.dataset.i;
        card.classList.toggle('open');
        if (card.classList.contains('open')) S.openExec.add(i); else S.openExec.delete(i);
      });
    });
    /* 恢复展开状态（运行过程中面板会频繁重绘） */
    box.querySelectorAll('.exec-node').forEach(card => {
      const i = +card.dataset.i;
      card.classList.toggle('open', S.openExec.has(i));
    });
    if (!S.openExec.size && S.runLog.length) {
      const f = box.querySelector('.exec-node');
      if (f) { f.classList.add('open'); S.openExec.add(0); }
    }
  }

  /* ------------------------------------------------------------------
     18. 单节点调试
     ------------------------------------------------------------------ */
  function debugNode(n) {
    const meta = ALL_NODES[n.type] || {};
    const body = `
      <div class="modal-head"><h3>单节点调试 · ${esc(n.cfg?.name || meta.name)}</h3><span class="x" data-close>×</span></div>
      <div class="modal-body">
        <div class="notice info" style="margin-bottom:12px">
          <span class="ico">ⓘ</span>
          <div>调试时模拟该节点的<b>上下文边界、工具白名单与资源锁环境</b>，无需运行完整工作流。</div>
        </div>
        <div class="field">
          <label>模拟输入数据</label>
          <textarea class="textarea" id="dbg-in" style="min-height:120px;font-family:var(--mono);font-size:11.5px">{
  "target": "pay-gateway",
  "branch": "feature/order-refactor",
  "changed_files": 12
}</textarea>
        </div>
        <div class="field">
          <label>调试范围</label>
          <select class="select" id="dbg-scope">
            <option>仅调试基础节点逻辑（不含能力包）</option>
            <option>包含能力包完整执行链</option>
          </select>
        </div>
        <div class="field">
          <label>模拟异步任务完成</label>
          <select class="select"><option>不模拟</option><option>模拟异步任务已完成</option></select>
        </div>
      </div>
      <div class="modal-foot">
        <button class="btn" data-close>取消</button>
        <button class="btn primary" id="dbg-run">▶ 运行调试</button>
      </div>`;
    const m = openModal(body);
    m.el.querySelector('#dbg-run').addEventListener('click', e => {
      const b = e.target;
      b.disabled = true; b.innerHTML = '<span class="spin"></span> 调试中…';
      setTimeout(() => {
        m.close();
        openModal(`
          <div class="modal-head"><h3>调试结果</h3><span class="x" data-close>×</span></div>
          <div class="modal-body">
            <div class="notice ok" style="margin-bottom:12px"><span class="ico">✓</span><div>节点执行成功，输出符合输出 Schema 约束，证据引用已通过平台校验。</div></div>
            <div class="exec-sec"><div class="lbl">输出</div><div class="code">${esc(buildOutput(n))}</div></div>
            <div class="exec-sec"><div class="lbl">耗时 / Token / 成本</div>
              <div class="code">duration: 1.24s · tokens: 3,182 · cost: $0.084</div></div>
          </div>
          <div class="modal-foot"><button class="btn primary" data-close>知道了</button></div>
        `, { size: 'wide' });
      }, 1400);
    });
  }

  /* ------------------------------------------------------------------
     19. 键盘
     ------------------------------------------------------------------ */
  function bindKeys() {
    window.addEventListener('keydown', e => {
      if (isTyping(e)) return;
      const meta = e.ctrlKey || e.metaKey;
      if (meta && e.key.toLowerCase() === 'z' && !e.shiftKey) { e.preventDefault(); undo(); }
      else if (meta && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) { e.preventDefault(); redo(); }
      else if (meta && e.key.toLowerCase() === 'c') { e.preventDefault(); copySelection(); }
      else if (meta && e.key.toLowerCase() === 'v') { e.preventDefault(); pasteSelection(); }
      else if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteSelection(); }
      else if (e.key === 'Escape') { S.sel.clear(); S.selEdge = null; render(); $('#validate-panel')?.classList.remove('show'); }
      else if (e.key === 'f' && !meta) { fitView(); }
      else if (meta && e.key === 's') { e.preventDefault(); $('#btn-save')?.click(); }
    });
  }

  /* ------------------------------------------------------------------
     导出
     ------------------------------------------------------------------ */
  window.ED = {
    state: S, init, render, fitView, validate, startRun, openConfig, addNode,
    nodeById, CAT_META, ALL_NODES, NODE_W, NODE_H,
  };

  document.addEventListener('DOMContentLoaded', init);
})();
