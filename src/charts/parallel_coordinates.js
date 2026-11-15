// Chart 4 component: parallel coordinates (one line per team) drawn on two canvases.
//   base canvas    axes, all lines, bin bars, tick labels (redrawn when data / size change)
//   overlay canvas hovered line, pinned lines, hovered bar outline (redrawn on every hover change)
// The data comes from build() in parallel_coordinates.py. Clicks go back to Python as the state
// value "click" = {cd: [kind, id, ...], nonce}: ["pin", team] or ["bin", axis key, bin index].

const STAGE_H = 470;
const PAD = { left: 64, top: 12, bottom: 34 };
const BAR_MIN = 6;
const BAR_MAX = 30;
const TICK_GAP = BAR_MIN / 2 + BAR_MAX / 2 + 4;   // tick labels sit left of the widest bar

// ── Helpers ──────────────────────────────────────────────────────────────────────────────────

function isTransparent(c) {
  return !c || c === "transparent" || /rgba\([^)]*,\s*0\)$/.test(c);
}

// First non-transparent background above the component (crosses the shadow-root boundary).
function pageBackground(el) {
  let node = el;
  while (node) {
    if (node instanceof Element) {
      const c = getComputedStyle(node).backgroundColor;
      if (!isTransparent(c)) return c;
    }
    node = node.parentElement || node.getRootNode?.().host || null;
  }
  return "#ffffff";
}

function readTheme(root) {
  const cs = getComputedStyle(root);
  return { text: cs.color, font: cs.fontFamily, bg: pageBackground(root) };
}

function isDark(color) {
  const [r, g, b] = (color.match(/\d+(\.\d+)?/g) || [255, 255, 255]).map(Number);
  return 0.299 * r + 0.587 * g + 0.114 * b < 128;
}

// Line colours and legend gradient for the current page theme (the scale's middle differs).
function applyThemeColors(ui, legendBar) {
  const dark = isDark(ui.theme.bg);
  ui.d.color = (dark ? ui.d.colorDark : ui.d.colorLight) || [];
  if (legendBar && ui.d.legend) {
    const stops = dark ? ui.d.legend.stopsDark : ui.d.legend.stopsLight;
    legendBar.style.background = `linear-gradient(to right, ${stops.join(", ")})`;
  }
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(x, y, w, h, r);
  else ctx.rect(x, y, w, h);
}

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

// ── Geometry ─────────────────────────────────────────────────────────────────────────────────

function layout(ui) {
  const { d } = ui;
  const W = ui.W;
  const right = Math.max(40, Math.min(170, W * 0.15));   // room for pinned-team labels
  const x0 = PAD.left;
  const x1 = W - right;
  const step = (x1 - x0) / (d.k - 1);
  const xs = Array.from({ length: d.k }, (_, a) => x0 + a * step);
  const top = PAD.top;
  const bot = STAGE_H - PAD.bottom;
  const yOf = (v) => bot - v * (bot - top);
  ui.g = { W, H: STAGE_H, xs, step, top, bot, yOf };

  // Pixel y of every line on every axis, so hover hit-testing is a cheap loop.
  const n = d.n || 0;
  const py = new Float32Array(n * d.k);
  for (let i = 0; i < n * d.k; i++) py[i] = yOf(d.ys[i]);
  ui.py = py;
}

function resize(ui) {
  const dpr = window.devicePixelRatio || 1;
  ui.W = Math.max(320, ui.stage.clientWidth || 800);
  for (const c of [ui.base, ui.over]) {
    c.width = Math.round(ui.W * dpr);
    c.height = Math.round(STAGE_H * dpr);
    c.getContext("2d").setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  layout(ui);
}

// ── Drawing ──────────────────────────────────────────────────────────────────────────────────

function linePath(ctx, ui, i) {
  const { d, g, py } = ui;
  const k = d.k;
  ctx.moveTo(g.xs[0], py[i * k]);
  for (let a = 1; a < k; a++) ctx.lineTo(g.xs[a], py[i * k + a]);
}

function drawBase(ui) {
  const { d, g, theme } = ui;
  const ctx = ui.base.getContext("2d");
  ctx.clearRect(0, 0, g.W, g.H);
  ctx.globalAlpha = 1;

  // Axes
  ctx.strokeStyle = theme.text;
  ctx.globalAlpha = 0.35;
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  for (const x of g.xs) { ctx.moveTo(x, g.top); ctx.lineTo(x, g.bot); }
  ctx.stroke();

  // Lines: teams outside the highlight in grey underneath, the rest in their own colour on top.
  // Rows arrive sorted by points per game, so the best teams are painted last (on top).
  ctx.lineJoin = "round";
  if (d.n) {
    if (d.hl) {
      ctx.strokeStyle = d.colors.neutral;
      ctx.globalAlpha = 0.12;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i < d.n; i++) if (!d.hl[i]) linePath(ctx, ui, i);
      ctx.stroke();
    }
    ctx.lineWidth = d.lineWidth;
    ctx.globalAlpha = d.lineAlpha;
    for (let i = 0; i < d.n; i++) {
      if (d.hl && !d.hl[i]) continue;
      ctx.strokeStyle = d.color[i];
      ctx.beginPath();
      linePath(ctx, ui, i);
      ctx.stroke();
    }
  }

  // Bin bars (histogram on each axis) and the highlighted share of each bin
  d.axes.forEach((axis, a) => {
    const x = g.xs[a];
    for (const bar of axis.bars) {
      const y = g.yOf(bar.y);
      const len = BAR_MIN + BAR_MAX * bar.len;
      const h = bar.chosen ? 12 : 9;
      ctx.globalAlpha = bar.chosen ? 0.5 : 0.45;
      ctx.fillStyle = bar.chosen ? d.colors.highlight : d.colors.neutral;
      roundRect(ctx, x - len / 2, y - h / 2, len, h, 2);
      ctx.fill();
      if (bar.chosen) {
        ctx.globalAlpha = 1;
        ctx.strokeStyle = d.colors.highlight;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
      if (bar.sel > 0) {
        const s = 4 + BAR_MAX * bar.sel;
        ctx.globalAlpha = 1;
        ctx.fillStyle = d.colors.highlight;
        roundRect(ctx, x - s / 2, y - 2.5, s, 5, 2);
        ctx.fill();
      }
    }
  });

  // Tick labels and axis titles
  ctx.fillStyle = theme.text;
  ctx.textBaseline = "middle";
  ctx.textAlign = "right";
  ctx.font = `10px ${theme.font}`;
  ctx.globalAlpha = 0.75;
  d.axes.forEach((axis, a) => {
    for (const [v, text] of axis.ticks) ctx.fillText(text, g.xs[a] - TICK_GAP, g.yOf(v));
  });
  ctx.globalAlpha = 1;
  ctx.textAlign = "center";
  ctx.font = `bold 12px ${theme.font}`;
  d.axes.forEach((axis, a) => ctx.fillText(axis.label, g.xs[a], g.bot + 20));

  if (!d.n) {
    ctx.font = `14px ${theme.font}`;
    ctx.globalAlpha = 0.7;
    ctx.fillText("No teams to show with the current filters.", g.W / 2, (g.top + g.bot) / 2);
  }
  ctx.globalAlpha = 1;
}

function pill(ctx, ui, text, x, y, border, align = "left", bold = false) {
  const { theme } = ui;
  ctx.font = `${bold ? "bold " : ""}11px ${theme.font}`;
  const w = ctx.measureText(text).width + 10;
  let left = align === "left" ? x : x - w;
  left = Math.max(2, Math.min(left, ui.g.W - w - 2));
  ctx.globalAlpha = 0.92;
  ctx.fillStyle = theme.bg;
  roundRect(ctx, left, y - 9, w, 18, 4);
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = border;
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.fillStyle = theme.text;
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  ctx.fillText(text, left + 5, y + 0.5);
}

function drawLine(ctx, ui, i, { values = false, label = false } = {}) {
  const { d, g, py, theme } = ui;
  const k = d.k;
  const color = d.color[i];
  ctx.lineJoin = "round";
  ctx.globalAlpha = 0.9;
  ctx.strokeStyle = theme.bg;           // halo so the line reads on top of the bundle
  ctx.lineWidth = 6;
  ctx.beginPath();
  linePath(ctx, ui, i);
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2.6;
  ctx.beginPath();
  linePath(ctx, ui, i);
  ctx.stroke();
  for (let a = 0; a < k; a++) {
    ctx.beginPath();
    ctx.arc(g.xs[a], py[i * k + a], 3.4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = theme.bg;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }
  if (values) {
    for (let a = 0; a < k; a++) pill(ctx, ui, d.txt[i * k + a], g.xs[a] + 8, py[i * k + a], color);
  }
  if (label) {
    pill(ctx, ui, `📌 ${d.teams[i]}`, g.xs[k - 1] + 10, py[i * k + k - 1], color, "left", true);
  }
}

function drawOver(ui) {
  const { d, g, theme } = ui;
  const ctx = ui.over.getContext("2d");
  ctx.clearRect(0, 0, g.W, g.H);
  if (!d.n) return;
  const hov = ui.hover;
  if (hov && hov.type === "line") {   // fade everything else so the hovered line can be followed
    ctx.globalAlpha = 0.55;
    ctx.fillStyle = theme.bg;
    ctx.fillRect(0, 0, g.W, g.H);
  }
  for (const team of ui.pins) {
    const i = ui.index.get(team);
    if (i !== undefined && !(hov && hov.type === "line" && hov.i === i)) drawLine(ctx, ui, i, { label: true });
  }
  if (hov && hov.type === "line") drawLine(ctx, ui, hov.i, { values: true });
  if (hov && hov.type === "bar") {
    const x = g.xs[hov.a];
    const y = g.yOf(hov.bar.y);
    const len = Math.max(BAR_MIN + BAR_MAX * hov.bar.len, 14) + 6;
    ctx.globalAlpha = 0.9;
    ctx.strokeStyle = theme.text;
    ctx.lineWidth = 1.5;
    roundRect(ctx, x - len / 2, y - 9, len, 18, 4);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

// ── Hit testing ──────────────────────────────────────────────────────────────────────────────

function hit(ui, mx, my) {
  const { d, g, py } = ui;
  const k = d.k;
  // Bars first: they sit on the axes, where lines are too crowded to pick anyway.
  for (let a = 0; a < d.axes.length; a++) {
    const x = g.xs[a];
    if (Math.abs(mx - x) > BAR_MAX / 2 + BAR_MIN + 4) continue;
    for (const bar of d.axes[a].bars) {
      const half = Math.max((BAR_MIN + BAR_MAX * bar.len) / 2, 8) + 2;
      if (Math.abs(mx - x) <= half && Math.abs(my - g.yOf(bar.y)) <= 7) return { type: "bar", a, bar };
    }
  }
  if (!d.n || mx < g.xs[0] || mx > g.xs[k - 1]) return null;

  // Lines: interpolate each line's y at the cursor's x. Pinned beat highlighted beat dimmed.
  const s = Math.min(k - 2, Math.floor((mx - g.xs[0]) / g.step));
  const t = (mx - g.xs[s]) / g.step;
  let best = -1, bestDist = Infinity, bestPri = -1;
  for (let i = 0; i < d.n; i++) {
    const pinned = ui.pins.has(d.teams[i]);
    const y0 = py[i * k + s];
    const dist = Math.abs(y0 + t * (py[i * k + s + 1] - y0) - my);
    const pri = pinned ? 2 : (!d.hl || d.hl[i]) ? 1 : 0;
    if (dist > [3, 5, 7][pri]) continue;
    if (pri > bestPri || (pri === bestPri && dist < bestDist)) {
      best = i; bestDist = dist; bestPri = pri;
    }
  }
  return best >= 0 ? { type: "line", i: best } : null;
}

function sameHit(a, b) {
  if (!a || !b) return a === b;
  return a.type === b.type && (a.type === "line" ? a.i === b.i : a.a === b.a && a.bar.bin === b.bar.bin);
}

// ── Tooltip ──────────────────────────────────────────────────────────────────────────────────

function showTip(ui, h, mx, my) {
  const { tip, d, theme } = ui;
  if (!h) { tip.style.display = "none"; return; }
  tip.replaceChildren();
  let title, lines, hint;
  if (h.type === "bar") {
    title = h.bar.title; lines = h.bar.body; hint = h.bar.hint;
  } else {
    title = d.teams[h.i];
    lines = [d.sub[h.i]];
    hint = ui.pins.has(title) ? "📌 Pinned · click to unpin" : "Click to pin (also shows in chart 5)";
  }
  tip.append(el("b", null, title));
  for (const line of lines) tip.append(document.createElement("br"), document.createTextNode(line));
  tip.append(document.createElement("br"), el("i", null, hint));
  tip.style.background = theme.bg;
  tip.style.color = theme.text;
  tip.style.display = "block";
  const w = tip.offsetWidth, hgt = tip.offsetHeight;
  const left = mx + 16 + w > ui.g.W ? mx - 16 - w : mx + 16;
  const top = Math.max(0, Math.min(my + 16, STAGE_H - hgt));
  tip.style.left = `${Math.max(0, left)}px`;
  tip.style.top = `${top}px`;
}

// ── Mount ────────────────────────────────────────────────────────────────────────────────────

export default function (component) {
  const { data, parentElement, setStateValue } = component;

  let root = parentElement.querySelector(".pc-root");
  if (!root) {
    root = el("div", "pc-root");
    const head = el("div", "pc-head");
    head.append(el("div", "pc-title"), el("div", "pc-legend"));
    const stage = el("div", "pc-stage");
    stage.append(el("canvas", "pc-base"), el("canvas", "pc-over"), el("div", "pc-tip"));
    root.append(head, stage);
    parentElement.appendChild(root);
    root._ui = {};
  }
  const ui = root._ui;
  ui.ctl?.abort();          // drop the listeners of the previous render
  ui.ro?.disconnect();
  ui.d = data;
  ui.pins = new Set(data.pins || []);
  ui.index = new Map((data.teams || []).map((t, i) => [t, i]));
  ui.hover = null;
  ui.stage = root.querySelector(".pc-stage");
  ui.base = root.querySelector(".pc-base");
  ui.over = root.querySelector(".pc-over");
  ui.tip = root.querySelector(".pc-tip");
  ui.tip.style.display = "none";
  ui.theme = readTheme(root);

  root.querySelector(".pc-title").textContent = data.title;
  const legend = root.querySelector(".pc-legend");
  legend.replaceChildren();
  ui.legendBar = null;
  if (data.legend) {
    ui.legendBar = el("span", "pc-gradient");
    legend.append(el("span", null, data.legend.label), el("span", "pc-muted", data.legend.lo), ui.legendBar,
                  el("span", "pc-muted", data.legend.hi));
  }
  applyThemeColors(ui, ui.legendBar);

  const redrawAll = () => { resize(ui); drawBase(ui); drawOver(ui); };
  redrawAll();

  const ctl = new AbortController();
  const opts = { signal: ctl.signal };
  ui.ctl = ctl;
  const ro = new ResizeObserver(() => {
    if (Math.max(320, ui.stage.clientWidth) !== ui.W) redrawAll();
  });
  ro.observe(ui.stage);
  ui.ro = ro;

  const update = () => {
    ui.raf = 0;
    const theme = readTheme(root);                    // light/dark switched since the last draw?
    if (theme.text !== ui.theme.text || theme.bg !== ui.theme.bg) {
      ui.theme = theme;
      applyThemeColors(ui, ui.legendBar);
      drawBase(ui);
    }
    const h = hit(ui, ui.mx, ui.my);
    if (!sameHit(h, ui.hover)) {
      ui.hover = h;
      drawOver(ui);
    }
    ui.over.style.cursor = h ? "pointer" : "default";
    showTip(ui, h, ui.mx, ui.my);
  };

  ui.over.addEventListener("mousemove", (e) => {
    ui.mx = e.offsetX;
    ui.my = e.offsetY;
    if (!ui.raf) ui.raf = requestAnimationFrame(update);
  }, opts);

  ui.over.addEventListener("mouseleave", () => {
    ui.hover = null;
    drawOver(ui);
    showTip(ui, null);
  }, opts);

  ui.over.addEventListener("click", (e) => {
    const h = hit(ui, e.offsetX, e.offsetY);
    if (!h) return;
    let cd;
    if (h.type === "bar") {
      cd = ["bin", ui.d.axes[h.a].key, h.bar.bin];
    } else {
      const team = ui.d.teams[h.i];
      cd = ["pin", team];
      // Show the pin straight away; Python confirms it on the rerun.
      if (ui.pins.has(team)) ui.pins.delete(team); else ui.pins.add(team);
      drawOver(ui);
      showTip(ui, h, e.offsetX, e.offsetY);
    }
    setStateValue("click", { cd, nonce: `${Date.now()}-${Math.random()}` });
  }, opts);

  // Only this render's own listeners/observer: a newer render may already have replaced them.
  return () => {
    ctl.abort();
    ro.disconnect();
  };
}
