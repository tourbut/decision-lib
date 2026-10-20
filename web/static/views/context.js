// context-gate: compact the labelled session, judge one memory write or the labelled set, run the gated agent.
import { api, badge, h, meter, runBusy } from "../common.js";


const ACTION = { keep: ["keep 원문", "go"], shrink: ["shrink 앞부분만", "hold"], drop: ["drop 비움", "out"] };
const TOTAL = { original: "원본", size_based: "크기 기반(앞 200자)", need_based: "필요도 기반(d3-flash)" };

function memoryBadge(d) {
  return d.allow ? badge("저장", "go") : badge("거절", d.source === "rule" ? "danger" : "out");
}

function memoryMeter(d, t) {
  return d.worth == null ? h("span", { class: "text" }, "모델 판정 없음")
    : h("div", { class: "meters" }, meter("기억할 가치", d.worth, { ticks: [t.block_below], over: d.worth < t.block_below }));
}

export async function contextView(root) {
  const setup = await api("/api/context-gate/setup");
  const t = setup.thresholds;

  // Compaction
  const compactBtn = h("button", { class: "primary" }, `도구 결과 ${setup.pairs.length}쌍 압축`);
  const compactStatus = h("p", { class: "status", role: "status" });
  const compactOut = h("div");
  compactBtn.addEventListener("click", () => runBusy(compactBtn, compactStatus, "쌍마다 판정 중", async () => {
    const data = await api("/api/context-gate/compact", {});
    const hits = data.rows.filter((r) => r.action === r.label).length;
    compactOut.replaceChildren(
      h("table", { class: "results" }, h("tbody", {}, Object.entries(data.totals).map(([k, v]) =>
        h("tr", {}, h("td", { class: "id" }, TOTAL[k]),
          h("td", {}, `${v.chars.toLocaleString()}자 · 꼭 필요한 사실 ${v.facts}/${setup.needed.length}`))))),
      h("p", {}, `라벨 일치 ${hits}/${data.rows.length}.`),
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "도구 호출과 압축 후 결과"), h("th", {}, "판정"), h("th", {}, "d3-flash 확률"))),
        h("tbody", {}, data.rows.map((r) => {
          const [label, tone] = ACTION[r.action];
          return h("tr", {},
            h("td", { class: "id" }, `${r.tool} ${Object.values(r.args)[0]}`,
              h("div", { class: "text redacted" }, r.after.length > 400 ? `${r.after.slice(0, 400)}…` : r.after)),
            h("td", {}, badge(label, tone),
              h("div", { class: "text" }, r.action === r.label ? "라벨과 일치" : `라벨: ${r.label}`)),
            h("td", {}, h("div", { class: "meters" },
              meter("결과 필요", r.scores.keep_result, { ticks: [t.keep_result], over: r.scores.keep_result >= t.keep_result }),
              meter("호출 기억", r.scores.keep_call, { ticks: [t.keep_call], over: r.scores.keep_call >= t.keep_call }))));
        }))));
  }));

  // One memory write
  const memText = h("input", { type: "text", value: setup.memories[0].text });
  const memBtn = h("button", { class: "primary" }, "저장 판정");
  const memStatus = h("p", { class: "status", role: "status" });
  const memOut = h("div");
  memBtn.addEventListener("click", () => runBusy(memBtn, memStatus, "판정 중", async () => {
    const d = await api("/api/context-gate/memory/check", { text: memText.value });
    memOut.replaceChildren(h("table", { class: "results" }, h("tbody", {}, h("tr", {},
      h("td", { class: "id" }, memoryBadge(d), h("div", { class: "text" }, d.reason)), h("td", {}, memoryMeter(d, t))))));
  }));
  memText.addEventListener("keydown", (e) => { if (e.key === "Enter") memBtn.click(); });

  // Live agent
  const message = h("textarea", { rows: 6, "aria-label": "에이전트에게 보낼 메시지" }, setup.live_message);
  const agentBtn = h("button", { class: "primary" }, "에이전트 실행");
  const agentStatus = h("p", { class: "status", role: "status" });
  const agentOut = h("div");
  agentBtn.addEventListener("click", () => runBusy(agentBtn, agentStatus, "로컬 LLM이 remember를 부르는 중", async () => {
    const data = await api("/api/context-gate/memory/agent", { message: message.value });
    agentOut.replaceChildren(
      data.log.length ? h("table", { class: "results" }, h("tbody", {}, data.log.map((d) => h("tr", {},
        h("td", { class: "id" }, d.text), h("td", {}, memoryBadge(d), h("div", { class: "text" }, d.reason)))))) :
        h("p", { class: "status" }, "에이전트가 remember를 부르지 않았다."),
      h("div", { class: "answer", "aria-label": "에이전트 답" }, data.answer));
  }));

  // Labelled memory set
  const evalBtn = h("button", { class: "primary" }, `라벨 ${setup.memories.length}건 판정`);
  const evalStatus = h("p", { class: "status", role: "status" });
  const evalOut = h("div");
  evalBtn.addEventListener("click", () => runBusy(evalBtn, evalStatus, "판정 중", async () => {
    const { rows } = await api("/api/context-gate/memory/eval", {});
    const hits = rows.filter((r) => r.allow === (r.label === "keep")).length;
    evalOut.replaceChildren(
      h("p", {}, `라벨 일치 ${hits}/${rows.length}.`),
      h("table", { class: "results" }, h("tbody", {}, rows.map((r) => h("tr", {},
        h("td", { class: "id" }, r.text, h("div", { class: "text" }, `라벨: ${r.label === "keep" ? "기억할 것" : "거를 것"}`)),
        h("td", {}, memoryBadge(r), h("div", { class: "text" }, r.reason)),
        h("td", {}, memoryMeter(r, t)))))));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "필요도 기반 압축"),
      h("p", { class: "text" }, `목표: ${setup.goal} 최근 요청: ${setup.latest}`),
      h("div", { class: "row" }, compactBtn, compactStatus),
      compactOut),
    h("section", { class: "run" },
      h("h3", {}, "메모리 저장 판정"),
      h("label", { class: "field" }, "저장할 문장", memText),
      h("div", { class: "row examples" }, "예시:",
        [0, 13, 19, 26].map((i) => h("button", { onclick: () => { memText.value = setup.memories[i].text; memBtn.click(); } },
          setup.memories[i].text))),
      h("div", { class: "row" }, memBtn, memStatus),
      memOut),
    h("section", { class: "run" },
      h("h3", {}, "메모리 게이트를 붙인 에이전트"),
      h("label", { class: "field" }, "메시지", message),
      h("div", { class: "row" }, agentBtn, agentStatus),
      agentOut),
    h("section", { class: "run" },
      h("h3", {}, "메모리 라벨 측정"),
      h("p", { class: "text" }, `기억할 가치가 ${t.block_below} 미만이면 거절한다. 키·비밀번호는 모델을 부르지 않고 정규식으로 거절한다.`),
      h("div", { class: "row" }, evalBtn, evalStatus),
      evalOut));
}
