// effort-router: run one turn through the router (optionally against the baselines), or route the labelled turns.
import { api, badge, h, meter, runBusy } from "../common.js";


const ROUTE = { fast: ["fast 추론 끔", "go"], think: ["think 추론 켬", "go"], handoff: ["handoff 이관", "hold"] };

function routeBadge(route) {
  const [label, tone] = ROUTE[route];
  return badge(label, tone);
}

function routeMeters(s, t) {
  if (!s || !Object.keys(s).length) return h("span", { class: "text" }, "모델 판정 없음");
  return h("div", { class: "meters" },
    meter("fast", s.route_fast),
    meter("think", s.route_think),
    meter("handoff", s.route_handoff),
    meter("확신도", s.confidence, { ticks: [t.confident], over: s.confidence < t.confident }),
    meter("외부 접근", s.needs_access, { ticks: [t.access_handoff], over: s.needs_access >= t.access_handoff }),
    meter("피해 위험", s.high_stakes, { ticks: [t.stakes_handoff], over: s.high_stakes >= t.stakes_handoff }));
}

function mark(r) {
  return r.correct == null ? "" : r.correct ? " · 정답" : " · 오답";
}

export async function effortView(root) {
  const setup = await api("/api/effort-router/setup");
  const t = setup.thresholds;
  const examples = [0, 10, 18, 20, 28, 31].map((i) => setup.turns[i].text);

  const text = h("input", { type: "text", value: examples[3] });
  const compare = h("input", { type: "checkbox" });
  const mode = h("select", { "aria-label": "라우터 모드" },
    [["on", "on: 판정대로 응답"], ["shadow", "shadow: 판정만 기록, think로 응답"], ["off", "off: 라우터 없이 think"]]
      .map(([v, l]) => h("option", { value: v }, l)));
  const runBtn = h("button", { class: "primary" }, "턴 실행");
  const runStatus = h("p", { class: "status", role: "status" });
  const out = h("div");

  runBtn.addEventListener("click", () => runBusy(runBtn, runStatus,
    compare.checked ? "라우팅, 항상 fast, 항상 think로 각각 답하는 중" : "판정하고 답하는 중", async () => {
      const data = await api("/api/effort-router/turn", { text: text.value, compare: compare.checked, mode: mode.value });
      const r = data.routed;
      const rows = [h("tr", {},
        h("td", { class: "id" }, r.mode === "on" ? "라우팅" : `라우팅(${r.mode}, 의도: ${r.intended})`, h("div", { class: "text" },
          `경로 ${r.tried.join(" → ")} · ${r.output_tokens}토큰 · ${r.seconds.toFixed(1)}초${mark(r)}`)),
        h("td", {}, h("div", { class: "answer" }, r.answer)))];
      for (const [name, b] of Object.entries(data.baselines ?? {})) {
        rows.push(h("tr", {},
          h("td", { class: "id" }, `항상 ${name}`, h("div", { class: "text" },
            `${b.output_tokens}토큰 · ${b.seconds.toFixed(1)}초${mark(b)}`)),
          h("td", {}, h("div", { class: "answer" }, b.answer))));
      }
      out.replaceChildren(
        h("table", { class: "results" }, h("tbody", {}, h("tr", {},
          h("td", { class: "id" }, routeBadge(r.route), h("div", { class: "text" }, r.reason)),
          h("td", {}, routeMeters(r.scores, t))))),
        data.key ? h("p", { class: "text" }, `라벨 세트의 턴이다. 정답 키: ${data.key}`) : "",
        h("table", { class: "results" }, h("tbody", {}, rows)));
    }));
  text.addEventListener("keydown", (e) => { if (e.key === "Enter") runBtn.click(); });

  const allBtn = h("button", { class: "primary" }, `라벨 ${setup.turns.length}턴 라우팅`);
  const allStatus = h("p", { class: "status", role: "status" });
  const allOut = h("div");
  allBtn.addEventListener("click", () => runBusy(allBtn, allStatus, "판정 중 (약 12초)", async () => {
    const { rows } = await api("/api/effort-router/route", {});
    const hits = rows.filter((r) => r.route === r.label).length;
    allOut.replaceChildren(
      h("p", {}, `라벨 일치 ${hits}/${rows.length}. LLM은 부르지 않고 경로만 판정했다.`),
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "턴"), h("th", {}, "경로"), h("th", {}, "d3-flash 판정"))),
        h("tbody", {}, rows.map((r) => h("tr", {},
          h("td", { class: "id" }, r.text),
          h("td", {}, routeBadge(r.route),
            h("div", { class: "text" }, r.reason),
            h("div", { class: "text" }, r.route === r.label ? "라벨과 일치" : `라벨: ${r.label}`)),
          h("td", {}, routeMeters(r.scores, t)))))));
  }));

  const shadowBtn = h("button", { class: "quiet" }, "shadow 비용 추정");
  const shadowOut = h("div");
  shadowBtn.addEventListener("click", () => runBusy(shadowBtn, allStatus, "라우터 판정만 모으는 중", async () => {
    const s = await api("/api/effort-router/shadow", {});
    shadowOut.replaceChildren(h("p", {},
      `${s.turns}턴에서 라우터 의도: fast ${s.intended.fast}, think ${s.intended.think}, handoff ${s.intended.handoff}. ` +
      `tiers.json 기준 비용: 항상 think ${s.fixed_cost.toFixed(2)} → 라우팅 ${s.routed_cost.toFixed(2)} (${Math.round(s.saving * 100)}% 절감 추정).`));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "턴 하나 실행"),
      h("label", { class: "field" }, "메시지 (effort: think 처럼 적으면 판정을 건너뜀)", text),
      h("div", { class: "row examples" }, "예시:",
        examples.map((q) => h("button", { onclick: () => { text.value = q; runBtn.click(); } }, q))),
      h("div", { class: "row" }, h("label", {}, "모드 ", mode), h("label", {}, compare, " 항상 fast·항상 think와 비교"), runBtn, runStatus),
      out),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정"),
      h("p", { class: "text" }, `턴 ${setup.turns.length}개에 직접 라벨을 붙였다. 확신도가 ${t.confident} 미만이면 think로, 외부 접근이나 피해 위험이 ${t.access_handoff} 이상이면 handoff로 보낸다. 눈금이 그 기준이다.`),
      h("div", { class: "row" }, allBtn, shadowBtn, allStatus),
      shadowOut,
      allOut));
}
