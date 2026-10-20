// citation-check: check one edited citation, the labelled set, or a cited answer from the local LLM.
import { api, badge, h, meter, runBusy } from "../common.js";


const VERDICT = {
  verified: ["verified 지지", "go"],
  contradicted: ["contradicted 반박", "danger"],
  unsupported: ["unsupported 근거 없음", "hold"],
  fabricated: ["fabricated 인용문 없음", "danger"],
};

function verdictBadge(verdict, prefix = "") {
  const [label, tone] = VERDICT[verdict];
  return badge(prefix + label, tone);
}

function relationMeters(r, autoAccept) {
  if (r.confidence == null) return h("span", { class: "text" }, "출처에서 인용문을 찾지 못해 모델을 부르지 않았다.");
  const p = r.probabilities;
  return h("div", { class: "meters" },
    meter("지지", p.supports, { over: r.verdict === "verified" }),
    meter("반박", p.contradicts, { over: r.verdict === "contradicted" }),
    meter("언급 없음", p.says_nothing, { over: r.verdict === "unsupported" }),
    meter("확신도", r.confidence, { ticks: [autoAccept], over: r.needs_review }));
}

function resultTable(citations, results, autoAccept, { labels = false } = {}) {
  return h("table", { class: "results" },
    h("thead", {}, h("tr", {}, h("th", {}, "주장과 인용"), h("th", {}, "판정"), h("th", {}, "d3-flash 확률"))),
    h("tbody", {}, citations.map((c, i) => {
      const r = results[i];
      return h("tr", {},
        h("td", { class: "id" }, c.claim,
          h("div", { class: "text" }, c.quote ? `«${c.quote}»` : "(인용문 없음)", ` §${c.section}`)),
        h("td", {},
          verdictBadge(r.verdict),
          r.needs_review ? h("div", {}, badge("사람 검토", "hold")) : null,
          labels ? h("div", { class: "text" }, c.label === r.verdict ? "라벨과 일치" : `라벨: ${c.label}`) : null,
          r.section && r.section !== c.section ? h("div", { class: "text" }, `인용문은 §${r.section}에 있음`) : null),
        h("td", {}, relationMeters(r, autoAccept)));
    })));
}

export async function citationView(root) {
  const setup = await api("/api/citation-check/setup");
  const auto = setup.auto_accept;

  // One citation, editable
  const pick = h("select", { "aria-label": "예시 인용" },
    setup.citations.map((c, i) => h("option", { value: i }, `[${c.label}] ${c.claim}`)));
  const claim = h("input", { type: "text", "aria-label": "주장" });
  const quote = h("textarea", { rows: 2, "aria-label": "인용문 (비우면 절 번호만 사용)" });
  const section = h("select", { "aria-label": "인용한 절" },
    Object.keys(setup.sections).map((n) => h("option", { value: n }, `§${n}`)));
  const oneBtn = h("button", { class: "primary" }, "검사");
  const oneStatus = h("p", { class: "status", role: "status" });
  const oneOut = h("div");
  function load(i) {
    const c = setup.citations[i];
    claim.value = c.claim;
    quote.value = c.quote ?? "";
    section.value = c.section;
  }
  pick.addEventListener("change", () => load(pick.value));
  load(0);
  oneBtn.addEventListener("click", () => runBusy(oneBtn, oneStatus, "검사 중", async () => {
    const c = { id: "edited", claim: claim.value, quote: quote.value || null, section: section.value };
    const { results } = await api("/api/citation-check/check", { citations: [c] });
    oneOut.replaceChildren(resultTable([c], results, auto));
  }));

  // Labelled set
  const evalBtn = h("button", { class: "primary" }, `라벨 ${setup.citations.length}건 검사`);
  const evalStatus = h("p", { class: "status", role: "status" });
  const evalOut = h("div");
  evalBtn.addEventListener("click", () => runBusy(evalBtn, evalStatus, "검사 중", async () => {
    const { results } = await api("/api/citation-check/eval", {});
    const hits = results.filter((r, i) => r.verdict === setup.citations[i].label).length;
    const review = results.filter((r) => r.needs_review).length;
    evalOut.replaceChildren(
      h("p", {}, `라벨 일치 ${hits}/${results.length}, 사람 검토 큐 ${review}건.`),
      resultTable(setup.citations, results, auto, { labels: true }));
  }));

  // LLM answer
  const question = h("input", { type: "text", value: setup.questions[0] });
  const askBtn = h("button", { class: "primary" }, "답변 생성 후 검사");
  const askStatus = h("p", { class: "status", role: "status" });
  const askOut = h("div");
  askBtn.addEventListener("click", () => runBusy(askBtn, askStatus, "로컬 LLM이 인용을 붙여 답하는 중", async () => {
    const data = await api("/api/citation-check/ask", { question: question.value });
    askOut.replaceChildren(resultTable(data.citations, data.results, auto));
  }));
  question.addEventListener("keydown", (e) => { if (e.key === "Enter") askBtn.click(); });

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "인용 하나 검사"),
      h("label", { class: "field" }, "예시", pick),
      h("label", { class: "field" }, "주장", claim),
      h("label", { class: "field" }, "인용문 (비우면 절 번호만 사용)", quote),
      h("div", { class: "row" }, h("label", {}, "인용한 절 ", section), oneBtn, oneStatus),
      oneOut),
    h("section", { class: "run" },
      h("h3", {}, "로컬 LLM 답변의 인용 검사"),
      h("label", { class: "field" }, "질문", question),
      h("div", { class: "row examples" }, "예시:",
        setup.questions.map((q) => h("button", { onclick: () => { question.value = q; askBtn.click(); } }, q))),
      h("div", { class: "row" }, askBtn, askStatus),
      askOut),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정"),
      h("p", { class: "text" }, `출처는 지어낸 사내 개인정보 처리 지침 ${Object.keys(setup.sections).length}개 절이다. 확신도가 ${auto} 미만이면 판정과 상관없이 사람 검토로 보낸다. 확신도 막대의 눈금이 그 기준이다.`),
      h("div", { class: "row" }, evalBtn, evalStatus),
      evalOut));
}
