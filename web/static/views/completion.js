// completion-check: check one edited end-of-turn snapshot, run the gated agent, or measure the labelled set.
import { api, badge, h, meter, runBusy } from "../common.js";


const ACTION = { pass: ["pass 통과", "go"], steer: ["steer 되돌림", "hold"], halt: ["halt 사람 호출", "danger"] };

function actionBadge(action) {
  const [label, tone] = ACTION[action];
  return badge(label, tone);
}

function checkMeters(s, t) {
  if (!s || !Object.keys(s).length) return h("span", { class: "text" }, "모델 판정 없음");
  return h("div", { class: "meters" },
    meter("사람 필요", s.needs_human, { ticks: [t.needs_human], over: s.needs_human >= t.needs_human }),
    meter("요구 충족", s.requirements_met, { ticks: [t.requirements_met], over: s.requirements_met < t.requirements_met }),
    meter("테스트 필요", s.needs_tests, { ticks: [t.needs_tests], over: s.needs_tests >= t.needs_tests }),
    meter("테스트 충분", s.tests_cover, { ticks: [t.tests_cover], over: s.needs_tests >= t.needs_tests && s.tests_cover < t.tests_cover }),
    meter("완료 주장", s.claims_done, { ticks: [t.claims_done], over: s.claims_done < t.claims_done }));
}

const testsText = (tests) => (tests ? `테스트 통과 ${tests.passed} · 실패 ${tests.failed}` : "테스트 실행 안 함");

function verdictCell(v) {
  return h("td", {}, actionBadge(v.action), v.reasons.map((r) => h("div", { class: "text" }, r)));
}

export async function completionView(root) {
  const setup = await api("/api/completion-check/setup");
  const t = setup.thresholds;

  // One snapshot, editable
  const pick = h("select", { "aria-label": "예시 상태" },
    setup.transcripts.map((x, i) => h("option", { value: i }, `[${x.label}] ${x.response.slice(0, 50)}`)));
  const task = h("textarea", { rows: 2, "aria-label": "과제" });
  const response = h("textarea", { rows: 3, "aria-label": "에이전트의 최종 답" });
  const changed = h("input", { type: "text", "aria-label": "변경 파일 (쉼표로 구분)" });
  const ran = h("input", { type: "checkbox" });
  const passed = h("input", { type: "number", min: 0, class: "narrow", "aria-label": "통과" });
  const failed = h("input", { type: "number", min: 0, class: "narrow", "aria-label": "실패" });
  const attempt = h("input", { type: "number", min: 1, max: 10, class: "narrow", "aria-label": "시도" });
  const oneBtn = h("button", { class: "primary" }, "판정");
  const oneStatus = h("p", { class: "status", role: "status" });
  const oneOut = h("div");
  function load(i) {
    const x = setup.transcripts[i];
    task.value = x.task;
    response.value = x.response;
    changed.value = x.changed.join(", ");
    ran.checked = x.tests != null;
    passed.value = x.tests?.passed ?? 0;
    failed.value = x.tests?.failed ?? 0;
    attempt.value = x.attempt;
  }
  pick.addEventListener("change", () => load(pick.value));
  load(0);
  oneBtn.addEventListener("click", () => runBusy(oneBtn, oneStatus, "판정 중", async () => {
    const v = await api("/api/completion-check/check", {
      task: task.value,
      response: response.value,
      changed: changed.value.split(",").map((s) => s.trim()).filter(Boolean),
      tests: ran.checked ? { passed: Number(passed.value), failed: Number(failed.value) } : null,
      attempt: Number(attempt.value),
    });
    oneOut.replaceChildren(
      h("table", { class: "results" }, h("tbody", {}, h("tr", {}, verdictCell(v), h("td", {}, checkMeters(v.scores, t))))),
      v.instruction ? h("div", { class: "answer", "aria-label": "에이전트에 보낼 지시" }, v.instruction) : "");
  }));

  // Live agent
  const agentTask = h("textarea", { rows: 7, "aria-label": "에이전트 과제" }, setup.task);
  const lazy = h("input", { type: "checkbox", checked: true });
  const agentBtn = h("button", { class: "primary" }, "에이전트 실행");
  const agentStatus = h("p", { class: "status", role: "status" });
  const agentOut = h("div");
  agentBtn.addEventListener("click", () => runBusy(agentBtn, agentStatus, "로컬 LLM이 쓰고 판정을 받는 중", async () => {
    const data = await api("/api/completion-check/agent", { task: agentTask.value, lazy: lazy.checked });
    agentOut.replaceChildren(
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "시도와 답"), h("th", {}, "판정"), h("th", {}, "d3-flash 확률"))),
        h("tbody", {}, data.attempts.map((a) => h("tr", {},
          h("td", { class: "id" }, `시도 ${a.attempt}`, h("div", { class: "text" }, a.response)),
          verdictCell(a),
          h("td", {}, checkMeters(a.scores, t)))))),
      h("div", { class: "answer", "aria-label": "최종 답" }, data.final));
  }));

  // Labelled set
  const evalBtn = h("button", { class: "primary" }, `라벨 ${setup.transcripts.length}건 판정`);
  const evalStatus = h("p", { class: "status", role: "status" });
  const evalOut = h("div");
  evalBtn.addEventListener("click", () => runBusy(evalBtn, evalStatus, "판정 중 (약 22초)", async () => {
    const { rows } = await api("/api/completion-check/eval", {});
    const hits = rows.filter((r) => r.action === r.label).length;
    evalOut.replaceChildren(
      h("p", {}, `라벨 일치 ${hits}/${rows.length}.`),
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "에이전트의 최종 답"), h("th", {}, "판정"), h("th", {}, "d3-flash 확률"))),
        h("tbody", {}, rows.map((r) => h("tr", {},
          h("td", { class: "id" }, r.response,
            h("div", { class: "text" }, `변경: ${r.changed.join(", ") || "없음"} · ${testsText(r.tests)} · 시도 ${r.attempt}`)),
          h("td", {}, actionBadge(r.action), r.reasons.map((x) => h("div", { class: "text" }, x)),
            h("div", { class: "text" }, r.action === r.label ? "라벨과 일치" : `라벨: ${r.label}`)),
          h("td", {}, checkMeters(r.scores, t)))))));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "턴 끝 상태 하나 판정"),
      h("label", { class: "field" }, "예시", pick),
      h("label", { class: "field" }, "과제", task),
      h("label", { class: "field" }, "에이전트의 최종 답", response),
      h("label", { class: "field" }, "변경 파일 (쉼표로 구분)", changed),
      h("div", { class: "row" },
        h("label", {}, ran, " 테스트 실행함"), h("label", {}, "통과 ", passed), h("label", {}, "실패 ", failed),
        h("label", {}, "시도 ", attempt), oneBtn, oneStatus),
      oneOut),
    h("section", { class: "run" },
      h("h3", {}, "완료 판정을 붙인 에이전트 실행"),
      h("label", { class: "field" }, "과제", agentTask),
      h("div", { class: "row" }, h("label", {}, lazy, " 첫 답을 일부러 덜 쓴 초안으로 바꾸기"), agentBtn, agentStatus),
      agentOut),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정"),
      h("p", { class: "text" }, `코딩 에이전트의 턴 끝 상태 ${setup.transcripts.length}건에 직접 라벨을 붙였다. 시도 ${setup.max_attempts}회째에도 빠진 것이 있으면 halt다. 남색 막대가 판정에 걸린 값이다.`),
      h("div", { class: "row" }, evalBtn, evalStatus),
      evalOut));
}
