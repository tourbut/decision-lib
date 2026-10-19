// Sample workbench UI. Every model-produced or user-entered string goes through
// textContent (via h()), never innerHTML: corpus text includes injection attempts.

const $ = (sel) => document.querySelector(sel);

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (v === true) el.setAttribute(k, "");
    else if (v !== false && v != null) el.setAttribute(k, v);
  }
  for (const c of children.flat()) if (c != null) el.append(c instanceof Node ? c : String(c));
  return el;
}

async function api(path, body) {
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
function meter(name, value, { max = 1, ticks = [], over = false } = {}) {
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

function badge(label, tone) {
  return h("span", { class: `route ${tone}` }, label);
}

function status(el, text, error = false) {
  el.textContent = text;
  el.classList.toggle("error", error);
}

async function runBusy(button, statusEl, label, fn) {
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

async function renderDiagrams(container, sources) {
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

// --- discovery-review --------------------------------------------------------------

const DECISION = {
  produce: ["제출", "go"],
  withhold: ["보류", "out"],
};

async function discoveryView(root) {
  const setup = await api("/api/discovery-review/setup");
  const t = setup.thresholds;
  let pages = setup.pages.map((p) => ({ ...p }));
  let threadId = null;
  const attorney = {}; // doc_id -> decision made in this run

  const protocol = h("textarea", { rows: 3 }, setup.protocol);
  const list = h("div", { class: "pages" });
  const runBtn = h("button", { class: "primary" }, "검토 실행");
  const runStatus = h("p", { class: "status", role: "status" });
  const decide = h("div");
  const results = h("div");

  function drawPages() {
    list.replaceChildren(...pages.map((p, i) => h("div", { class: "page-edit" },
      h("div", { class: "meta" },
        h("input", { type: "text", value: p.doc_id, "aria-label": `${i + 1}번 페이지 문서 ID`,
          oninput: (e) => { p.doc_id = e.target.value; } }),
        p.expect ? h("span", {}, `예상 분기: ${p.expect}`) : null),
      h("textarea", { rows: 4, "aria-label": `${p.doc_id} 본문`,
        oninput: (e) => { p.page = e.target.value; } }, p.page),
      h("button", { class: "quiet", onclick: () => { pages.splice(i, 1); drawPages(); } }, "빼기"))));
  }

  function draw(report) {
    threadId = report.thread_id;
    const done = Object.fromEntries(report.results.map((r) => [r.doc_id, r]));
    const waiting = Object.fromEntries(report.pending.map((p) => [p.doc_id, p]));

    results.replaceChildren(h("table", { class: "results" },
      h("thead", {}, h("tr", {}, h("th", {}, "문서"), h("th", {}, "처리"), h("th", {}, "d3-flash 판정"))),
      h("tbody", {}, pages.map((p) => {
        const s = report.scores[p.doc_id];
        const r = done[p.doc_id];
        const w = waiting[p.doc_id];
        let outcome;
        if (w) outcome = badge("변호사 검토 대기", "hold");
        else if (r) {
          const [label, tone] = DECISION[r.decision];
          outcome = badge(r.redacted ? `${label} (레드랙션)` : label, tone);
        } else outcome = badge("실행 안 함", "out");
        return h("tr", {},
          h("td", { class: "id" }, p.doc_id,
            p.expect ? h("div", { class: "text" }, `예상: ${p.expect}`) : null),
          h("td", {}, outcome,
            attorney[p.doc_id] ? h("div", { class: "text" }, `변호사 결정: ${DECISION[attorney[p.doc_id]][0]}`) : null,
            w?.residual_pii != null ? h("div", { class: "text" }, `레드랙션 후 잔여 PII ${w.residual_pii.toFixed(2)}`) : null,
            r?.redacted ? h("div", { class: "redacted" }, r.page) : null),
          h("td", {}, s ? h("div", { class: "meters" },
            meter("특권", s.privileged, { ticks: [t.privileged], over: s.privileged > t.privileged }),
            meter("관련성(0–2)", s.responsive, { max: 2, ticks: [t.not_responsive, t.responsive],
              over: s.responsive >= t.not_responsive && s.responsive < t.responsive }),
            meter("관련성 확신", s.responsive_confidence, { ticks: [t.responsive_confidence],
              over: s.responsive_confidence < t.responsive_confidence }),
            meter("개인정보", s.contains_pii, { ticks: [t.contains_pii], over: s.contains_pii > t.contains_pii }),
          ) : "—"));
      }))));

    if (!report.pending.length) return decide.replaceChildren();
    const choice = {};
    const submit = h("button", { class: "primary" }, "결정 반영하고 재개");
    const decideStatus = h("p", { class: "status", role: "status" });
    decide.replaceChildren(h("div", { class: "decide" },
      h("h3", {}, `변호사 검토 ${report.pending.length}건`),
      h("p", { class: "text" }, "그래프가 interrupt()로 멈춰 있다. 페이지마다 결정을 고르면 체크포인트에서 이어 간다. 검토 요청에는 문서 ID와 점수만 담긴다."),
      report.pending.map((p) => h("fieldset", {},
        h("legend", {}, p.doc_id),
        ["produce", "withhold"].map((d) => h("label", {},
          h("input", { type: "radio", name: `d-${p.id}`, value: d,
            onchange: () => { choice[p.id] = d; } }), ` ${DECISION[d][0]}`)))),
      h("div", { class: "row" }, submit, decideStatus)));
    submit.addEventListener("click", () => runBusy(submit, decideStatus, "재개 중", async () => {
      if (Object.keys(choice).length !== report.pending.length) throw new Error("모든 페이지에 결정을 골라야 한다.");
      for (const p of report.pending) attorney[p.doc_id] = choice[p.id];
      draw(await api("/api/discovery-review/resume", { thread_id: threadId, decisions: choice }));
    }));
  }

  runBtn.addEventListener("click", () => runBusy(runBtn, runStatus, "d3-flash로 분류하는 중", async () => {
    for (const k of Object.keys(attorney)) delete attorney[k];
    const ids = pages.map((p) => p.doc_id.trim());
    if (new Set(ids).size !== ids.length) throw new Error("문서 ID가 겹친다. 서로 다른 ID를 쓴다.");
    draw(await api("/api/discovery-review/run", {
      protocol: protocol.value,
      pages: pages.map((p) => ({ doc_id: p.doc_id.trim(), page: p.page })),
    }));
  }));

  drawPages();
  root.append(
    h("section", { class: "run" },
      h("label", { class: "field" }, "검토 기준", protocol),
      h("div", { class: "field" }, h("strong", {}, `페이지 ${pages.length}개 (가상 문서, 고쳐서 실행할 수 있다)`), list),
      h("div", { class: "row" },
        h("button", { class: "quiet", onclick: () => { pages.push({ doc_id: `NEW-${pages.length + 1}`, page: "" }); drawPages(); } }, "페이지 추가"),
        runBtn, runStatus)),
    decide, results);
}

// --- rag-passage-filter ------------------------------------------------------------

const ROUTE = {
  evidence: ["채택 근거", "go"],
  conflict: ["충돌 근거", "hold"],
  excluded_injection: ["제외: 인젝션", "danger"],
  excluded_off_topic: ["제외: 주제 밖", "out"],
  excluded_no_evidence: ["제외: 근거 없음", "out"],
};

async function ragView(root) {
  const setup = await api("/api/rag-passage-filter/setup");
  const t = setup.thresholds;

  const query = h("input", { type: "text", value: setup.examples[0] });
  const topK = h("input", { type: "number", min: 1, max: 12, value: 6, class: "narrow" });
  const generate = h("input", { type: "checkbox", checked: true });
  const runBtn = h("button", { class: "primary" }, "질의 실행");
  const runStatus = h("p", { class: "status", role: "status" });
  const answer = h("div");
  const results = h("div");

  async function go() {
    const data = await api("/api/rag-passage-filter/query", {
      query: query.value, top_k: Number(topK.value), generate: generate.checked,
    });
    answer.replaceChildren(data.answer ? h("div", { class: "answer", "aria-label": "생성된 답변" }, data.answer) : "");
    if (!data.passages.length) {
      return results.replaceChildren(h("p", { class: "status" }, "검색된 문단이 없다. 다른 낱말로 질의한다."));
    }
    results.replaceChildren(h("table", { class: "results" },
      h("thead", {}, h("tr", {}, h("th", {}, "문단"), h("th", {}, "경로"), h("th", {}, "d3-flash 판정"))),
      h("tbody", {}, data.passages.map((p) => {
        const s = p.scores;
        const [label, tone] = ROUTE[p.route];
        return h("tr", {},
          h("td", { class: "id" }, p.id, h("div", { class: "text" }, p.title), h("div", { class: "text" }, p.text)),
          h("td", {}, badge(label, tone)),
          h("td", {}, h("div", { class: "meters" },
            meter("인젝션", s.contains_prompt_injection, { ticks: [t.injection_max], over: s.contains_prompt_injection > t.injection_max }),
            meter("전제 충돌", s.contradicts_query_premise, { ticks: [t.contradicts_min], over: s.contradicts_query_premise > t.contradicts_min }),
            meter("관련성", s.is_relevant, { ticks: [t.relevant_min], over: s.is_relevant < t.relevant_min }),
            meter("근거", s.contains_answer_evidence, { ticks: [t.evidence_min], over: s.contains_answer_evidence > t.evidence_min }))));
      }))));
  }

  runBtn.addEventListener("click", () => runBusy(runBtn, runStatus, "검색하고 문단을 분류하는 중", go));
  query.addEventListener("keydown", (e) => { if (e.key === "Enter") runBtn.click(); });

  root.append(
    h("section", { class: "run" },
      h("label", { class: "field" }, "질의", query),
      h("div", { class: "row examples" }, "예시:",
        setup.examples.map((q) => h("button", { onclick: () => { query.value = q; runBtn.click(); } }, q))),
      h("div", { class: "row" },
        h("label", {}, "검색 문단 수 ", topK),
        h("label", {}, generate, " 로컬 LLM으로 답변 생성"),
        runBtn, runStatus),
      h("p", { class: "text" }, `코퍼스는 가상 사내 문서 ${setup.passages.length}문단이다. 눈금은 분기 임계값, 남색 막대는 그 규칙에 걸린 값이다. 규칙은 인젝션 → 전제 충돌 → 관련성 → 근거 순으로 처음 걸린 것 하나만 적용된다.`)),
    answer, results);
}

// --- Shell ---------------------------------------------------------------------------

const VIEWS = { "discovery-review": discoveryView, "rag-passage-filter": ragView };

async function show(sample) {
  const main = $("#main");
  for (const b of document.querySelectorAll("#nav button")) b.setAttribute("aria-current", String(b.dataset.id === sample.id));
  const diagrams = h("div", { class: "diagrams" });
  const flow = h("details", { class: "flow" }, h("summary", {}, `처리 흐름 (다이어그램 ${sample.diagrams.length}개)`), diagrams);
  flow.addEventListener("toggle", () => {
    if (flow.open && !diagrams.childElementCount) renderDiagrams(diagrams, sample.diagrams);
  });
  const body = h("div");
  main.replaceChildren(h("header", {}, h("h2", {}, sample.title), h("p", {}, sample.summary)), flow, body);
  history.replaceState(null, "", `#${sample.id}`);
  try {
    await VIEWS[sample.id](body);
  } catch (e) {
    body.append(h("p", { class: "status error" }, e.message));
  }
}

async function boot() {
  try {
    const [samples, models] = await Promise.all([api("/api/samples"), api("/api/models")]);
    $("#models").replaceChildren(`판정: ${models.decision}`, h("br"), `생성: ${models.llm || "설정 안 됨"}`);
    $("#nav").replaceChildren(...samples.map((s) =>
      h("button", { "data-id": s.id, onclick: () => show(s) }, s.id, h("small", {}, s.summary))));
    show(samples.find((s) => `#${s.id}` === location.hash) ?? samples[0]);
  } catch (e) {
    status($("#boot"), `서버에 연결하지 못했다: ${e.message}`, true);
  }
}

boot();
