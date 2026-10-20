// decision-calibration: one ticket across option orders, then the two benchmarks' metrics.
import { api, badge, h, meter, runBusy } from "../common.js";


const METHOD = {
  choice: "Choice (부정, 긍정 순)",
  choice_reversed: "Choice (긍정, 부정 순)",
  noul: "Noul (긍정인가?)",
  first_order: "첫 순서만",
  l0: "L0 보정 (순서 4개 평균 ÷ 사전확률)",
};

const pct = (x) => `${(x * 100).toFixed(1)}%`;
const top = (p) => Object.keys(p).reduce((a, b) => (p[a] >= p[b] ? a : b));

// Metric rows carry their own labels: on a phone the table header is hidden.
function metricTable(methods, threshold) {
  return h("table", { class: "results" },
    h("tbody", {}, Object.entries(methods).map(([name, m]) => {
      const r = m.review.find((x) => x.threshold === threshold);
      return h("tr", {},
        h("td", { class: "id" }, METHOD[name]),
        h("td", {}, `정확도 ${pct(m.accuracy)} · ECE ${m.ece.toFixed(3)} · Brier ${m.brier.toFixed(3)}`,
          h("div", { class: "text" }, `확률 ${threshold} 미만 사람 검토 ${pct(r.review_rate)} · 자동 처리분 정확도 ${r.auto_accuracy == null ? "-" : pct(r.auto_accuracy)}`)),
        h("td", {}, h("div", { class: "meters" }, m.bins.map((b) =>
          meter(`${b.lo.toFixed(1)}–${b.hi.toFixed(1)} (${b.n}건)`, b.accuracy, { ticks: [b.confidence] })))));
    })));
}

function thresholdPicker(thresholds, onChange) {
  const sel = h("select", { "aria-label": "사람 검토 기준 확률" },
    thresholds.map((t) => h("option", { value: t, selected: t === 0.9 }, String(t))));
  sel.addEventListener("change", () => onChange(Number(sel.value)));
  return h("label", {}, "사람 검토 기준 확률 ", sel);
}

function orderRows(orders, probs, labels) {
  return orders.map((order, i) => {
    const p = probs[i];
    return h("tr", {},
      h("td", { class: "id" }, `순서 ${i + 1}`, h("div", { class: "text" }, order.join(" → "))),
      h("td", {}, badge(top(p), "go")),
      h("td", {}, h("div", { class: "meters" }, labels.map((k) => meter(k, p[k], { over: k === top(p) })))));
  });
}

export async function calibrationView(root) {
  const setup = await api("/api/decision-calibration/setup");
  const labels = Object.keys(setup.labels);
  const thresholds = setup.review_thresholds;

  // One ticket
  const text = h("textarea", { rows: 2, "aria-label": "문의" }, setup.tickets[18].text);
  const oneBtn = h("button", { class: "primary" }, "순서 4가지로 판정");
  const oneStatus = h("p", { class: "status", role: "status" });
  const oneOut = h("div");
  oneBtn.addEventListener("click", () => runBusy(oneBtn, oneStatus, "판정 중", async () => {
    const data = await api("/api/decision-calibration/one", { text: text.value });
    const picks = new Set(data.probabilities.map(top));
    oneOut.replaceChildren(
      h("p", {}, picks.size > 1 ? `순서에 따라 판정이 바뀌었다: ${[...picks].join(", ")}` : "순서를 바꿔도 판정이 같았다."),
      h("table", { class: "results" }, h("tbody", {}, orderRows(data.orders, data.probabilities, labels))));
  }));

  // Routing benchmark
  const routeBtn = h("button", { class: "primary" }, `문의 ${setup.tickets.length}건 측정`);
  const routeStatus = h("p", { class: "status", role: "status" });
  const routeOut = h("div");
  routeBtn.addEventListener("click", () => runBusy(routeBtn, routeStatus, `${setup.tickets.length * labels.length}회 호출 중 (약 25초)`, async () => {
    const r = await api("/api/decision-calibration/routing", {});
    const table = h("div");
    const draw = (t) => table.replaceChildren(metricTable(r.methods, t));
    draw(0.9);
    routeOut.replaceChildren(
      h("p", {}, `순서에 따라 판정이 바뀐 문의 ${r.flipped.length}건(${pct(r.flip_rate)}). 호출 1건 ${r.seconds_per_call.toFixed(2)}초.`),
      h("div", { class: "meters" }, r.position_picks.map((p, i) =>
        meter(`${i + 1}번째 선택지`, p, { ticks: [1 / labels.length] }))),
      h("div", { class: "row" }, thresholdPicker(thresholds, draw)),
      table,
      r.flipped.length ? h("p", {}, "순서에 따라 판정이 바뀐 문의") : "",
      r.flipped.length ? h("table", { class: "results" }, h("tbody", {}, r.flipped.map((f) => h("tr", {},
        h("td", { class: "id" }, f.text, h("div", { class: "text" }, `라벨 ${f.label}`)),
        h("td", {}, f.orders.map((p, i) => h("div", {}, `순서 ${i + 1}: `, badge(top(p), top(p) === f.label ? "go" : "hold")))))))) : "");
  }));

  // Sentiment benchmark
  const limit = h("input", { type: "number", min: 10, max: setup.nsmc_size, value: 60, class: "narrow" });
  const sentBtn = h("button", { class: "primary" }, "NSMC 측정");
  const sentStatus = h("p", { class: "status", role: "status" });
  const sentOut = h("div");
  sentBtn.addEventListener("click", () => runBusy(sentBtn, sentStatus, `${Number(limit.value) * 3}회 호출 중`, async () => {
    const s = await api("/api/decision-calibration/sentiment", { limit: Number(limit.value) });
    const table = h("div");
    const draw = (t) => table.replaceChildren(metricTable(s.methods, t));
    draw(0.9);
    sentOut.replaceChildren(
      h("p", {}, `리뷰 ${s.n}건. 선택지 순서를 바꿔 판정이 바뀐 리뷰 ${s.flipped.length}건(${pct(s.flip_rate)}).`),
      h("div", { class: "row" }, thresholdPicker(thresholds, draw)),
      table,
      s.flipped.map((f) => h("p", { class: "text" },
        `[라벨 ${f.label}] ${f.text} — 긍정 확률 ${f.orders.map((p) => p.positive.toFixed(2)).join(" / ")}`)));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "문의 하나를 선택지 순서 4가지로"),
      h("label", { class: "field" }, "문의", text),
      h("div", { class: "row examples" }, "예시:",
        [18, 4, 28, 0].map((i) => h("button", { onclick: () => { text.value = setup.tickets[i].text; oneBtn.click(); } },
          setup.tickets[i].text))),
      h("div", { class: "row" }, oneBtn, oneStatus),
      oneOut),
    h("section", { class: "run" },
      h("h3", {}, "문의 라우팅: 순서 편향과 L0 보정"),
      h("p", { class: "text" }, "팀마다 10건씩 직접 만든 문의다. 위치별 막대의 눈금은 쏠림이 없을 때의 비율이다. 신뢰도 막대는 확률 구간별 실제 정답률이고, 눈금은 그 구간의 평균 확률이다. 막대 끝이 눈금에 가까울수록 확률을 그대로 믿을 수 있다."),
      h("div", { class: "row" }, routeBtn, routeStatus),
      routeOut),
    h("section", { class: "run" },
      h("h3", {}, "감성 분류: Choice와 Noul의 보정"),
      h("p", { class: "text" }, `NSMC 공개 리뷰(CC0) ${setup.nsmc_size}건 중 앞에서부터 N건을 쓴다. 리뷰마다 3회 호출한다.`),
      h("div", { class: "row" }, h("label", {}, "리뷰 수 ", limit), sentBtn, sentStatus),
      sentOut));
}
