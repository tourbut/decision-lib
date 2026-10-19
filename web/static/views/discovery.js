// discovery-review: edit pages, run the review graph, and resume it with attorney decisions.
import { api, badge, h, meter, runBusy } from "../common.js";


const DECISION = {
  produce: ["제출", "go"],
  withhold: ["보류", "out"],
};

export async function discoveryView(root) {
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
