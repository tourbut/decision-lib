// order-sim: dry-run the four policies on one synthetic order book and compare.
import { api, badge, h, runBusy } from "../common.js";


export async function orderView(root) {
  const setup = await api("/api/order-sim/setup");
  const blocks = h("input", { type: "number", min: 20, max: 300, value: 100, class: "narrow" });
  const seed = h("input", { type: "number", min: 0, max: 10000, value: 7, class: "narrow" });
  const budget = h("input", { type: "number", min: 10, max: 2000, value: setup.budget_ms, class: "narrow" });
  const runBtn = h("button", { class: "primary" }, "dry run");
  const runStatus = h("p", { class: "status", role: "status" });
  const out = h("div");

  runBtn.addEventListener("click", () => runBusy(runBtn, runStatus, "블록마다 판정 중(d3-flash 블록당 약 0.16초)", async () => {
    const data = await api("/api/order-sim/run", { blocks: Number(blocks.value), seed: Number(seed.value), budget_ms: Number(budget.value) });
    out.replaceChildren(h("table", { class: "results" },
      h("thead", {}, h("tr", {}, h("th", {}, "정책"), h("th", {}, "손익·거래"), h("th", {}, "막힌 결정"))),
      h("tbody", {}, Object.entries(data.results).map(([name, r]) => h("tr", {},
        h("td", { class: "id" }, name, r.stopped_at != null ? h("div", {}, badge(`블록 ${r.stopped_at}에서 손실 한도`, "danger")) : null),
        h("td", {}, badge(`손익 ${r.pnl >= 0 ? "+" : ""}${r.pnl.toFixed(4)}`, r.pnl > 0 ? "go" : r.pnl < 0 ? "danger" : "out"),
          h("div", { class: "text" }, `거래 ${r.trades} · 적중 ${r.hit_rate == null ? "-" : Math.round(r.hit_rate * 100) + "%"} · 최종 포지션 ${r.position}`),
          h("div", { class: "text" }, `매수 ${r.counts.buy} · 매도 ${r.counts.sell} · 보류 ${r.counts.hold}`)),
        h("td", {}, h("div", { class: "text" }, `늦은 결정 ${r.counts.late} · 포지션 한도 ${r.counts.position_cap} · 중단 뒤 ${r.counts.after_stop}`),
          h("div", { class: "text" }, `결정 p50 ${(r.p50_seconds * 1000).toFixed(0)}ms`)))))));
  }));

  root.append(h("section", { class: "run" },
    h("p", { class: "text" }, `실제 주문은 없다. 합성 시장은 주문장 불균형이 다음 가격 변화를 일부 정하도록 만들었다. 포지션 한도 ±${setup.max_position}, 누적 손실 ${setup.loss_limit}에서 정리 후 중단, 결정이 예산보다 늦으면 보류.`),
    h("div", { class: "row" }, h("label", {}, "블록 ", blocks), h("label", {}, "seed ", seed), h("label", {}, "결정 예산(ms) ", budget), runBtn, runStatus),
    out));
}
