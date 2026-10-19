// Shared helpers for the sample views. Every model-produced or user-entered string goes through
// textContent (via h()), never innerHTML: corpus text includes injection attempts.

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) el.append(c instanceof Node ? c : String(c));
  return el;
}

export async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(", ") : data.detail;
    throw new Error(detail || `요청 실패 (${res.status})`);
  }
  return data;
}

// A probability bar with its routing thresholds as ticks. `over` marks a value that
// triggered its rule, so the reason for a route is visible without reading numbers.
export function meter(name, value, { max = 1, ticks = [], over = false } = {}) {
  const pct = (x) => `${Math.max(0, Math.min(1, x / max)) * 100}%`;
  return h("div", { class: "meter" },
    h("span", { class: "name" }, name),
    h("div", {
      class: `bar${over ? " over" : ""}`,
      role: "img",
      "aria-label": `${name} ${value.toFixed(2)}, 기준 ${ticks.join(", ")}${over ? ", 규칙에 걸림" : ""}`,
    },
      h("span", { class: "fill", style: `width:${pct(value)}` }),
      ticks.map((t) => h("span", { class: "tick", style: `left:calc(${pct(t)} - 1px)` }))),
    h("span", { class: "value" }, value.toFixed(2)));
}

export function badge(label, tone) {
  return h("span", { class: `route ${tone}` }, label);
}

export function status(el, text, error = false) {
  el.textContent = text;
  el.classList.toggle("error", error);
}

export async function runBusy(button, statusEl, label, fn) {
  button.disabled = true;
  status(statusEl, label);
  const started = performance.now();
  try {
    await fn();
    status(statusEl, `완료 (${((performance.now() - started) / 1000).toFixed(1)}초)`);
  } catch (e) {
    status(statusEl, e.message, true);
  } finally {
    button.disabled = false;
  }
}

// --- Mermaid diagrams from each sample README -------------------------------------

// Vendored (static/vendor, mermaid 11.4.1, MIT) so diagrams render without internet.
let mermaidLoad;
function loadMermaid() {
  mermaidLoad ??= new Promise((resolve, reject) => {
    const s = h("script", { src: "/static/vendor/mermaid.min.js" });
    s.onload = () => resolve(window.mermaid);
    s.onerror = () => reject(new Error("mermaid.min.js를 불러오지 못했다"));
    document.head.append(s);
  });
  return mermaidLoad;
}

export async function renderDiagrams(container, sources) {
  try {
    const mermaid = await loadMermaid();
    const dark = matchMedia("(prefers-color-scheme: dark)").matches;
    mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "neutral", securityLevel: "strict" });
    container.replaceChildren();
    for (const [i, src] of sources.entries()) {
      const { svg } = await mermaid.render(`diagram-${Date.now()}-${i}`, src);
      const box = h("div");
      box.innerHTML = svg; // mermaid output (strict mode), from our own README
      container.append(box);
    }
  } catch (e) {
    container.replaceChildren(
      h("p", { class: "status error" }, `다이어그램을 그리지 못했다: ${e.message}. 원문을 표시한다.`),
      ...sources.map((s) => h("pre", {}, s)));
  }
}
