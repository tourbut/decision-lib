// rerank: rerank one SciFact query or a typed claim, then view the candidates in any of the orders.
import { api, badge, h, meter, runBusy } from "../common.js";


const ORDER = {
  bm25: "BM25 그대로",
  relevance: "관련도 루브릭(10단계)",
  evidence: "근거 루브릭(3단계, 사용자 정의)",
  "bm25+relevance": "BM25 + 관련도 RRF 결합",
};

export async function rerankView(root) {
  const setup = await api("/api/rerank/setup");

  const pick = h("select", { "aria-label": "SciFact 질의" },
    setup.queries.map((q) => h("option", { value: q.id }, `q${q.id} ${q.text}`)));
  const own = h("input", { type: "text", placeholder: "직접 쓴 주장(영어). 비우면 위 질의를 쓴다", "aria-label": "직접 쓴 주장" });
  const depth = h("input", { type: "number", min: 5, max: 30, value: 20, class: "narrow" });
  const runBtn = h("button", { class: "primary" }, "리랭킹");
  const runStatus = h("p", { class: "status", role: "status" });
  const out = h("div");

  runBtn.addEventListener("click", () => runBusy(runBtn, runStatus, `후보 ${depth.value}개를 채점하는 중 (1개 약 0.5초)`, async () => {
    const body = own.value.trim() ? { text: own.value.trim() } : { query_id: pick.value };
    const data = await api("/api/rerank/query", { ...body, depth: Number(depth.value) });
    if (!data.rows.length) return out.replaceChildren(h("p", { class: "status" }, "BM25 후보가 없다. 다른 낱말로 쓴다."));
    const byId = Object.fromEntries(data.rows.map((r) => [r.id, r]));
    const bm25Rank = Object.fromEntries(data.rankings.bm25.map((d, i) => [d, i + 1]));
    const table = h("div");
    const order = h("select", { "aria-label": "보기 순서" },
      Object.entries(ORDER).map(([k, label]) => h("option", { value: k, selected: k === "relevance" }, label)));
    const draw = () => table.replaceChildren(h("table", { class: "results" },
      h("thead", {}, h("tr", {}, h("th", {}, "순위와 문서"), h("th", {}, "정답"), h("th", {}, "d3-flash 점수"))),
      h("tbody", {}, data.rankings[order.value].map((d, i) => {
        const r = byId[d];
        return h("tr", {},
          h("td", { class: "id" }, `${i + 1}. ${r.title}`,
            h("div", { class: "text" }, `BM25 ${bm25Rank[d]}위 · ${r.text.slice(0, 220)}…`)),
          h("td", {}, r.relevant ? badge("정답", "go") : data.metrics ? badge("오답", "out") : "-"),
          h("td", {}, h("div", { class: "meters" },
            meter("관련도(0–9)", r.relevance, { max: 9 }),
            meter("근거(0–2)", r.evidence, { max: 2 }))));
      }))));
    order.addEventListener("change", draw);
    draw();
    out.replaceChildren(
      data.metrics ? h("table", { class: "results" }, h("tbody", {}, Object.entries(data.metrics).map(([k, m]) =>
        h("tr", {}, h("td", { class: "id" }, ORDER[k]),
          h("td", {}, `nDCG@10 ${m["ndcg@10"].toFixed(3)} · recall@10 ${m["recall@10"].toFixed(3)}`))))) :
        h("p", { class: "text" }, "직접 쓴 주장에는 정답 라벨이 없어 nDCG를 계산하지 않는다."),
      h("div", { class: "row" }, h("label", {}, "보기 순서 ", order)),
      table);
  }));

  root.append(h("section", { class: "run" },
    h("label", { class: "field" }, "SciFact 질의(주장)", pick),
    h("label", { class: "field" }, "또는 직접 쓴 주장", own),
    h("div", { class: "row" }, h("label", {}, "후보 수 ", depth), runBtn, runStatus),
    h("p", { class: "text" }, `SciFact(CC BY-NC 2.0) 테스트 질의 ${setup.queries.length}개와 BM25 후보 초록 ${setup.docs}개를 담았다. 직접 쓴 주장은 이 초록 안에서 BM25로 후보를 찾는다.`),
    out));
}
