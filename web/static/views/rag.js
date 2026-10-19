// rag-passage-filter: run a query and show each retrieved passage with its route and scores.
import { api, badge, h, meter, runBusy } from "../common.js";


const ROUTE = {
  evidence: ["채택 근거", "go"],
  conflict: ["충돌 근거", "hold"],
  excluded_injection: ["제외: 인젝션", "danger"],
  excluded_off_topic: ["제외: 주제 밖", "out"],
  excluded_no_evidence: ["제외: 근거 없음", "out"],
};

export async function ragView(root) {
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
