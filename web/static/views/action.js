// action-picker: run one goal (or all goals) in an environment and show every step the picker took.
import { api, badge, h, meter, runBusy } from "../common.js";


function outcome(r) {
  if (r.ok) return badge(r.impossible ? "보류 성공" : "도착 확인", "go");
  if (r.stopped === "DONE") return badge("DONE 주장 실패", "danger");
  return badge(r.impossible ? "보류 안 함" : "보류·중단", "hold");
}

function traceTable(r) {
  return h("table", { class: "results" },
    h("thead", {}, h("tr", {}, h("th", {}, "관찰"), h("th", {}, "고른 행동"))),
    h("tbody", {}, r.trace.map((t, i) => h("tr", {},
      h("td", { class: "id" }, `${i + 1}단계`, h("div", { class: "text redacted" }, t.observation)),
      h("td", {}, t.action === "DONE" || t.action === "NONE" ? badge(t.action, t.action === "DONE" ? "go" : "hold") : t.label,
        h("div", { class: "meters" }, meter("확률", t.probability)))))));
}

function runBlock(r) {
  const facts = [
    `${r.trace.length}단계`,
    r.moves != null ? `걸은 칸 ${r.moves} (최단 경로 행동 ${r.shortest}개 중 이동 ${r.shortest - 2})` : null,
    r.replans?.length ? `계획 교체: ${r.replans.join(" / ")}` : null,
  ].filter(Boolean).join(" · ");
  return h("div", { class: "run-block" },
    h("p", {}, outcome(r), " ", r.goal),
    h("p", { class: "text" }, facts),
    r.map ? h("pre", { class: "map", "aria-label": "지도" }, r.map.join("\n")) : null,
    r.dry_run?.length ? h("p", { class: "text" }, `실행 기록(dry run): ${r.dry_run.join(" → ")}`) : null,
    traceTable(r));
}

export async function actionView(root) {
  const setup = await api("/api/action-picker/setup");

  const env = h("select", { "aria-label": "환경" },
    Object.entries(setup.envs).map(([k, v]) => h("option", { value: k }, v)));
  const goal = h("select", { "aria-label": "목표" });
  const fillGoals = () => goal.replaceChildren(...setup.goals[env.value].map((g, i) => h("option", { value: i }, g)));
  env.addEventListener("change", fillGoals);
  fillGoals();

  const oneBtn = h("button", { class: "primary" }, "이 목표 실행");
  const allBtn = h("button", { class: "quiet" }, "이 환경의 목표 전부 실행");
  const runStatus = h("p", { class: "status", role: "status" });
  const out = h("div");

  async function go(index) {
    const { runs } = await api("/api/action-picker/run", { env: env.value, index });
    const okCount = runs.filter((r) => r.ok).length;
    out.replaceChildren(
      runs.length > 1 ? h("p", {}, `성공 ${okCount}/${runs.length}.`) : "",
      ...runs.map(runBlock));
  }
  oneBtn.addEventListener("click", () => runBusy(oneBtn, runStatus, "행동을 고르는 중", () => go(Number(goal.value))));
  allBtn.addEventListener("click", () => runBusy(allBtn, runStatus, "모든 목표를 실행하는 중", () => go(null)));

  root.append(h("section", { class: "run" },
    h("div", { class: "row" }, h("label", {}, "환경 ", env)),
    h("label", { class: "field" }, "목표", goal),
    h("div", { class: "row" }, oneBtn, allBtn, runStatus),
    h("p", { class: "text" }, `후보는 지금 가능한 행동만이다. 최고 확률이 ${setup.confident} 미만이면 멈춘다(NONE). DONE은 코드가 제목·설정 값·출구 위치로 따로 확인한다.`),
    out));
}
