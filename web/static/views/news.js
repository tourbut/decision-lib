// news-match: score a feed against the profiles, then move the threshold without new model calls.
import { api, badge, h, meter, runBusy } from "../common.js";


function picksAt(scores, t) {
  return scores.map((row) => Object.keys(row).filter((k) => row[k] >= t).sort());
}

function precisionRecall(picked, labels) {
  const key = (i, t) => `${i}|${t}`;
  const pred = new Set(picked.flatMap((ts, i) => ts.map((t) => key(i, t))));
  const truth = new Set(labels.flatMap((ts, i) => ts.map((t) => key(i, t))));
  const hit = [...pred].filter((p) => truth.has(p)).length;
  return { precision: pred.size ? hit / pred.size : 1, recall: truth.size ? hit / truth.size : 1, picked: pred.size, relevant: truth.size };
}

export async function newsView(root) {
  const setup = await api("/api/news-match/setup");
  const topics = setup.topics;

  const pasted = h("textarea", { rows: 4, "aria-label": "직접 넣을 헤드라인(한 줄에 하나)", placeholder: "비우면 예시 피드 40개를 쓴다" });
  const runBtn = h("button", { class: "primary" }, "매칭");
  const runStatus = h("p", { class: "status", role: "status" });
  const threshold = h("select", { "aria-label": "기준 점수" },
    [1.0, 1.5, 2.0, 2.5].map((t) => h("option", { value: t, selected: t === setup.threshold }, String(t))));
  const summary = h("p");
  const out = h("div");
  let data = null;

  function draw() {
    if (!data) return;
    const t = Number(threshold.value);
    const picked = picksAt(data.scores, t);
    if (data.labels) {
      const m = precisionRecall(picked, data.labels);
      summary.textContent = `기준 ${t}: 고른 쌍 ${m.picked}개(맞춰야 할 쌍 ${m.relevant}개), 정밀도 ${m.precision.toFixed(2)}, 재현율 ${m.recall.toFixed(2)}. 헤드라인 ${data.headlines.length}개에 ${data.seconds.toFixed(1)}초.`;
    } else {
      summary.textContent = `기준 ${t}: 고른 쌍 ${picked.flat().length}개. 헤드라인 ${data.headlines.length}개에 ${data.seconds.toFixed(1)}초.`;
    }
    out.replaceChildren(h("table", { class: "results" },
      h("thead", {}, h("tr", {}, h("th", {}, "헤드라인"), h("th", {}, "보낼 주제"), h("th", {}, "주제별 점수(0–3)"))),
      h("tbody", {}, data.headlines.map((text, i) => {
        const want = data.labels?.[i];
        const same = want && JSON.stringify([...want].sort()) === JSON.stringify(picked[i]);
        return h("tr", {},
          h("td", { class: "id" }, text, want ? h("div", { class: "text" }, `라벨: ${want.length ? want.join(", ") : "없음"}${same ? "" : " · 다름"}`) : null),
          h("td", {}, picked[i].length ? picked[i].map((p) => badge(p, "go")) : badge("없음", "out")),
          h("td", {}, h("div", { class: "meters" }, Object.keys(topics).map((k) =>
            meter(k, data.scores[i][k], { max: 3, ticks: [t], over: data.scores[i][k] >= t })))));
      }))));
  }
  threshold.addEventListener("change", draw);
  runBtn.addEventListener("click", () => runBusy(runBtn, runStatus, "헤드라인마다 판정 중", async () => {
    const lines = pasted.value.split("\n").map((s) => s.trim()).filter(Boolean);
    data = await api("/api/news-match/match", lines.length ? { headlines: lines } : {});
    draw();
  }));

  root.append(h("section", { class: "run" },
    h("p", { class: "text" }, Object.entries(topics).map(([k, v]) => `${k}: ${v}`).join(" / ")),
    h("label", { class: "field" }, "직접 넣을 헤드라인(선택)", pasted),
    h("div", { class: "row" }, runBtn, h("label", {}, "기준 점수 ", threshold), runStatus),
    summary,
    out));
}
