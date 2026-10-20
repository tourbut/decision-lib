// judgment-tools: call one MCP tool with JSON arguments, or measure a labelled set through MCP.
import { api, badge, h, runBusy } from "../common.js";


const TONE = { pass: "go", APPROVE: "go", review: "hold", ESCALATE: "hold", block: "danger", DENY: "danger" };

function headline(r) {
  const key = ["recommendation", "decision", "handler", "relation", "choice"].find((k) => r[k] != null);
  if (key) return badge(`${key}: ${r[key]}`, TONE[r[key]] ?? "out");
  return r.yes != null ? badge(`yes ${r.yes.toFixed(2)}`, "out") : badge(`score ${r.score.toFixed(2)}`, "out");
}

export async function judgmentView(root) {
  const setup = await api("/api/judgment-tools/setup");

  const tool = h("select", { "aria-label": "도구" }, setup.tools.map((t) => h("option", { value: t.name }, t.name)));
  const describe = h("p", { class: "text" });
  const args = h("textarea", { rows: 6, "aria-label": "인자 (JSON)" });
  const load = () => {
    describe.textContent = setup.tools.find((t) => t.name === tool.value).description;
    args.value = JSON.stringify(setup.examples[tool.value], null, 2);
  };
  tool.addEventListener("change", load);
  tool.value = "approval";
  load();
  const callBtn = h("button", { class: "primary" }, "MCP로 호출");
  const callStatus = h("p", { class: "status", role: "status" });
  const callOut = h("div");
  callBtn.addEventListener("click", () => runBusy(callBtn, callStatus, "tools/call 중", async () => {
    let parsed;
    try { parsed = JSON.parse(args.value); } catch { throw new Error("인자는 JSON 객체여야 한다."); }
    const r = await api("/api/judgment-tools/call", { tool: tool.value, arguments: parsed });
    callOut.replaceChildren(
      h("p", {}, headline(r), r.reason ? ` ${r.reason}` : "", r.answer ? ` → ${r.answer}` : "", r.plan ? ` → ${r.plan}` : ""),
      h("pre", { class: "answer" }, JSON.stringify(r, null, 2)));
  }));

  const evalOut = h("div");
  const evalStatus = h("p", { class: "status", role: "status" });
  const evalButtons = Object.entries(setup.sets).map(([name, n]) => {
    const b = h("button", { class: "quiet" }, `${name} ${n}건`);
    b.addEventListener("click", () => runBusy(b, evalStatus, "측정 중", async () => {
      const { rows, field } = await api("/api/judgment-tools/eval", { tool: name });
      const hits = rows.filter((r) => r.result[field] === r.label).length;
      evalOut.replaceChildren(
        h("p", {}, `${name}: 라벨 일치 ${hits}/${rows.length}.`),
        h("table", { class: "results" }, h("tbody", {}, rows.map((r) => h("tr", {},
          h("td", { class: "id" }, Object.values(r.input).join(" ↔ "), h("div", { class: "text" }, `라벨: ${r.label}`)),
          h("td", {}, headline(r.result), h("div", { class: "text" }, r.result.reason ?? r.result.plan ?? ""),
            r.result.answer ? h("div", { class: "text" }, `로컬 답: ${r.result.answer}`) : null))))));
    }));
    return b;
  });

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "도구 하나 호출"),
      h("div", { class: "row" }, h("label", {}, "도구 ", tool)),
      describe,
      h("label", { class: "field" }, "인자 (JSON)", args),
      h("div", { class: "row" }, callBtn, callStatus),
      h("p", { class: "text" }, "웹 서버가 MCP 서버를 같은 프로세스에 띄우고 MCP 클라이언트로 tools/call을 보낸다. 결과의 advisory_only·execution_authorized를 보라."),
      callOut),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정 (MCP 경유)"),
      h("div", { class: "row" }, ...evalButtons, evalStatus),
      evalOut));
}
