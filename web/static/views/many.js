// many-options: suggest at most one skill, or pick one of 448 time zones through regions.
import { api, badge, h, meter, runBusy } from "../common.js";


function top(p, n) {
  return Object.entries(p).sort((a, b) => b[1] - a[1]).slice(0, n);
}

function skillCell(s) {
  return h("td", {}, s.skill ? badge(s.skill, "go") : badge("추천 안 함", "out"), h("div", { class: "text" }, s.reason));
}

function skillMeters(s, t) {
  return h("div", { class: "meters" },
    top(s.stage1, 3).map(([k, v]) => meter(`1단계 ${k}`, v)),
    Object.entries(s.fits).map(([k, v]) => meter(`적합 ${k}`, v, { ticks: [t.fit], over: v >= t.fit })));
}

function zoneMeters(z, t) {
  return h("div", { class: "meters" },
    top(z.group_probabilities, 3).map(([k, v]) => meter(k, v, { ticks: [t.second_group], over: z.groups.includes(k) })),
    meter("시간대 확률", z.probability));
}

function zoneCell(z) {
  return h("td", {}, badge(z.choice, "go"),
    h("div", { class: "text" }, `지역 ${z.groups.join(" + ")}에서 ${z.options_asked}개 중 고름`));
}

function section(title, input, examples, runBtn, status, out, note) {
  return h("section", { class: "run" },
    h("h3", {}, title),
    h("label", { class: "field" }, "요청", input),
    h("div", { class: "row examples" }, "예시:",
      examples.map((q) => h("button", { onclick: () => { input.value = q; runBtn.click(); } }, q))),
    h("div", { class: "row" }, runBtn, status),
    h("p", { class: "text" }, note),
    out);
}

export async function manyView(root) {
  const setup = await api("/api/many-options/setup");
  const t = setup.thresholds;

  // Skills
  const skillText = h("input", { type: "text", value: setup.skill_requests[0].text });
  const skillBtn = h("button", { class: "primary" }, "스킬 추천");
  const skillStatus = h("p", { class: "status", role: "status" });
  const skillOut = h("div");
  skillBtn.addEventListener("click", () => runBusy(skillBtn, skillStatus, "판정 중", async () => {
    const s = await api("/api/many-options/skill", { text: skillText.value });
    skillOut.replaceChildren(h("table", { class: "results" }, h("tbody", {}, h("tr", {}, skillCell(s), h("td", {}, skillMeters(s, t))))));
  }));
  skillText.addEventListener("keydown", (e) => { if (e.key === "Enter") skillBtn.click(); });

  // Zones
  const zoneText = h("input", { type: "text", value: setup.zone_requests[5].text });
  const zoneBtn = h("button", { class: "primary" }, "시간대 고르기");
  const zoneStatus = h("p", { class: "status", role: "status" });
  const zoneOut = h("div");
  zoneBtn.addEventListener("click", () => runBusy(zoneBtn, zoneStatus, "지역 → 시간대 순서로 판정 중", async () => {
    const z = await api("/api/many-options/zone", { text: zoneText.value });
    zoneOut.replaceChildren(h("table", { class: "results" }, h("tbody", {}, h("tr", {}, zoneCell(z), h("td", {}, zoneMeters(z, t))))));
  }));
  zoneText.addEventListener("keydown", (e) => { if (e.key === "Enter") zoneBtn.click(); });

  // Labelled sets
  const evalOut = h("div");
  const evalStatus = h("p", { class: "status", role: "status" });
  const skillEval = h("button", { class: "primary" }, `스킬 ${setup.skill_requests.length}건 측정`);
  const zoneEval = h("button", { class: "primary" }, `시간대 ${setup.zone_requests.length}건 측정`);
  skillEval.addEventListener("click", () => runBusy(skillEval, evalStatus, "판정 중 (약 21초)", async () => {
    const { rows } = await api("/api/many-options/skill/eval", {});
    const want = (r) => (r.label === "none" ? null : r.label);
    const hits = rows.filter((r) => r.skill === want(r)).length;
    const stage1 = rows.filter((r) => r.stage1_pick === want(r)).length;
    evalOut.replaceChildren(
      h("p", {}, `라벨 일치: 1단계만 ${stage1}/${rows.length}, 재검토 포함 ${hits}/${rows.length}.`),
      h("table", { class: "results" }, h("tbody", {}, rows.map((r) => h("tr", {},
        h("td", { class: "id" }, r.text, h("div", { class: "text" }, `라벨: ${r.label}`)),
        skillCell(r), h("td", {}, skillMeters(r, t)))))));
  }));
  zoneEval.addEventListener("click", () => runBusy(zoneEval, evalStatus, "판정 중 (약 22초)", async () => {
    const { rows } = await api("/api/many-options/zone/eval", {});
    const hits = rows.filter((r) => r.choice === r.label).length;
    evalOut.replaceChildren(
      h("p", {}, `라벨 일치 ${hits}/${rows.length}.`),
      h("table", { class: "results" }, h("tbody", {}, rows.map((r) => h("tr", {},
        h("td", { class: "id" }, r.text, h("div", { class: "text" }, `라벨: ${r.label}`)),
        zoneCell(r), h("td", {}, zoneMeters(r, t)))))));
  }));

  root.append(
    section("스킬 추천 (최대 1개)", skillText, [0, 19, 31, 35].map((i) => setup.skill_requests[i].text),
      skillBtn, skillStatus, skillOut,
      `가상 스킬 ${Object.keys(setup.skills).length}개. 1단계에서 none이 1위면 멈추고, 아니면 상위 3개의 적합도가 ${t.fit} 이상인 것 하나만 추천한다.`),
    section(`계층 선택 (시간대 ${setup.zone_count}개)`, zoneText, [5, 18, 26, 37].map((i) => setup.zone_requests[i].text),
      zoneBtn, zoneStatus, zoneOut,
      `d3-flash는 Choice 하나에 선택지를 255개까지 받는다. 지역 ${Object.keys(setup.regions).length}개를 먼저 고르고, 1위 지역 확률이 ${t.second_group} 미만이면 2위 지역도 함께 본다.`),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정"),
      h("div", { class: "row" }, skillEval, zoneEval, evalStatus),
      evalOut));
}
