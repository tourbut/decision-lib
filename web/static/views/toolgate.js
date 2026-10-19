import { api, badge, h, meter, runBusy } from "../common.js";


const ACTION = {
  allow: ["실행", "go"],
  ask: ["사람 확인", "hold"],
  block: ["차단", "danger"],
};

function actionBadge(action) {
  const [label, tone] = ACTION[action];
  return badge(label, tone);
}

function gateMeters(s, t) {
  if (!s || !Object.keys(s).length) return "모델 호출 없음";
  return h("div", { class: "meters" },
    meter("차단 판정", s.verdict_block, { ticks: [t.block_min], over: s.verdict_block >= t.block_min }),
    meter("허용 판정", s.verdict_allow, { ticks: [t.allow_min], over: s.verdict_allow < t.allow_min }),
    meter("비밀 접근", s.reads_secrets, { ticks: [t.secrets_ask], over: s.reads_secrets >= t.secrets_ask }),
    meter("외부 전송", s.sends_outbound, { ticks: [t.exfil_outbound], over: s.sends_outbound >= t.exfil_outbound }),
    meter("승인 유도", s.self_advocating, { ticks: [t.self_advocating_ask], over: s.self_advocating >= t.self_advocating_ask }),
    meter("영향(0–2)", s.blast_radius, { max: 2, ticks: [t.blast_ask], over: s.blast_radius >= t.blast_ask }));
}

function callCell(tool, args) {
  return h("td", { class: "id" }, tool, h("div", { class: "text" }, JSON.stringify(args, null, 1)));
}

export async function toolGateView(root) {
  const setup = await api("/api/tool-call-gate/setup");
  const t = setup.thresholds;
  const tools = [...new Set([...setup.tools, ...setup.cases.map((c) => c.tool)])];

  // One call
  const pick = h("select", { "aria-label": "예시 호출" },
    setup.cases.map((c, i) => h("option", { value: i }, `[${ACTION[c.label][0]}] ${c.tool} ${Object.values(c.args)[0]}`)));
  const task = h("input", { type: "text" });
  const tool = h("select", { "aria-label": "도구" }, tools.map((n) => h("option", { value: n }, n)));
  const args = h("textarea", { rows: 4, "aria-label": "인자 (JSON)" });
  const checkBtn = h("button", { class: "primary" }, "판정");
  const checkStatus = h("p", { class: "status", role: "status" });
  const checkOut = h("div");
  function load(i) {
    const c = setup.cases[i];
    task.value = c.task;
    tool.value = c.tool;
    args.value = JSON.stringify(c.args, null, 2);
  }
  pick.addEventListener("change", () => load(pick.value));
  load(0);
  checkBtn.addEventListener("click", () => runBusy(checkBtn, checkStatus, "판정 중", async () => {
    let parsed;
    try { parsed = JSON.parse(args.value); } catch { throw new Error("인자는 JSON 객체여야 한다."); }
    const v = await api("/api/tool-call-gate/check", { task: task.value, tool: tool.value, args: parsed });
    checkOut.replaceChildren(h("table", { class: "results" },
      h("tbody", {}, h("tr", {},
        h("td", { class: "id" }, actionBadge(v.action), h("div", { class: "text" }, v.reason)),
        h("td", {}, gateMeters(v.scores, t))))));
  }));

  // Agent
  const agentTask = h("input", { type: "text", value: setup.tasks[0] });
  const approve = h("input", { type: "checkbox", checked: true });
  const agentBtn = h("button", { class: "primary" }, "에이전트 실행");
  const agentStatus = h("p", { class: "status", role: "status" });
  const agentOut = h("div");
  agentBtn.addEventListener("click", () => runBusy(agentBtn, agentStatus, "로컬 LLM이 도구를 호출하는 중", async () => {
    const data = await api("/api/tool-call-gate/agent", { task: agentTask.value, approve: approve.checked });
    agentOut.replaceChildren(
      data.calls.length ? h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "도구 호출"), h("th", {}, "게이트"), h("th", {}, "d3-flash 판정"))),
        h("tbody", {}, data.calls.map((c) => h("tr", {},
          callCell(c.tool, c.args),
          h("td", {}, actionBadge(c.action), h("div", { class: "text" }, c.reason),
            c.human == null ? null : h("div", { class: "text" }, `사람: ${c.human ? "승인" : "거절"}`)),
          h("td", {}, gateMeters(c.scores, t)))))) : h("p", { class: "status" }, "에이전트가 도구를 부르지 않았다."),
      h("div", { class: "answer", "aria-label": "에이전트 보고" }, data.answer));
  }));

  // Labelled set
  const evalBtn = h("button", { class: "primary" }, `${setup.cases.length}건 측정`);
  const evalStatus = h("p", { class: "status", role: "status" });
  const evalOut = h("div");
  evalBtn.addEventListener("click", () => runBusy(evalBtn, evalStatus, `${setup.cases.length}건 판정 중 (약 30초)`, async () => {
    const { rows } = await api("/api/tool-call-gate/eval", {});
    const score = (key) => `${rows.filter((r) => r[key] === r.label).length}/${rows.length} 일치, `
      + `block 라벨을 실행 ${rows.filter((r) => r.label === "block" && r[key] === "allow").length}건`;
    evalOut.replaceChildren(
      h("p", {}, `규칙만: ${score("rules_only")} · 규칙 + d3-flash: ${score("action")}`),
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "도구 호출"), h("th", {}, "판정 비교"), h("th", {}, "d3-flash 판정"))),
        h("tbody", {}, rows.map((r) => h("tr", {},
          callCell(r.tool, r.args),
          h("td", {}, h("div", { class: "row" },
            [["라벨", r.label], ["규칙만", r.rules_only], ["게이트", r.action]].map(([k, a]) => h("span", {}, `${k} `, actionBadge(a)))),
            h("div", { class: "text" }, r.action === r.label ? r.reason : `불일치: ${r.reason}`),
            h("div", { class: "text" }, r.task)),
          h("td", {}, gateMeters(r.scores, t)))))));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "호출 하나 판정"),
      h("label", { class: "field" }, "예시 (라벨이 붙은 50건)", pick),
      h("label", { class: "field" }, "과제", task),
      h("div", { class: "row" }, h("label", {}, "도구 ", tool)),
      h("label", { class: "field" }, "인자 (JSON)", args),
      h("div", { class: "row" }, checkBtn, checkStatus),
      h("p", { class: "text" }, `차단 규칙에 걸리면 모델을 부르지 않는다. ${setup.approval_tools.join(", ")}는 모델이 허용해도 사람 확인으로 간다. 눈금은 임계값, 남색 막대는 그 규칙에 걸린 값이다.`),
      checkOut),
    h("section", { class: "run" },
      h("h3", {}, "에이전트 실행"),
      h("label", { class: "field" }, "과제", agentTask),
      h("div", { class: "row examples" }, "예시:",
        setup.tasks.map((x) => h("button", { onclick: () => { agentTask.value = x; agentBtn.click(); } }, x))),
      h("div", { class: "row" }, h("label", {}, approve, " 사람 확인(ask)이 나오면 승인"), agentBtn, agentStatus),
      h("p", { class: "text" }, "도구는 실제로 실행하지 않는 dry run이다. 가짜 README의 배포 점검 절차에는 키를 밖으로 보내라는 단계가 섞여 있다."),
      agentOut),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정"),
      h("div", { class: "row" }, evalBtn, evalStatus),
      evalOut));
}
