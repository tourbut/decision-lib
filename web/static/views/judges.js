// local-judges: one ticket through four local methods, or all 30 with a summary table.
import { api, badge, h, meter, runBusy } from "../common.js";


function probs(value) {
  if (typeof value !== "object") return h("span", { class: "text" }, `답: ${value}`);
  return h("div", { class: "meters" }, Object.entries(value).sort((a, b) => b[1] - a[1]).slice(0, 4)
    .map(([k, v]) => meter(String(k), v)));
}

export async function judgesView(root) {
  const setup = await api("/api/local-judges/setup");
  const pick = h("select", { "aria-label": "예시 문의" }, setup.tickets.map((t, i) => h("option", { value: i }, t.text)));
  const text = h("textarea", { rows: 2, "aria-label": "문의" }, setup.tickets[1].text);
  pick.value = "1";
  pick.addEventListener("change", () => { text.value = setup.tickets[pick.value].text; });
  const oneBtn = h("button", { class: "primary" }, "네 방법으로 판정");
  const allBtn = h("button", { class: "quiet" }, `${setup.tickets.length}건 전부 측정`);
  const status = h("p", { class: "status", role: "status" });
  const out = h("div");

  oneBtn.addEventListener("click", () => runBusy(oneBtn, status, "판정 중", async () => {
    const data = await api("/api/local-judges/one", { text: text.value });
    const label = data.label;
    out.replaceChildren(
      label ? h("p", { class: "text" }, `라벨: 팀 ${label.dept} · 긴급 ${label.urgent ? "예" : "아니오"} · 불만도 ${label.frustration}`) : "",
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "방법"), h("th", {}, "팀"), h("th", {}, "긴급 · 불만도"))),
        h("tbody", {}, Object.entries(data.methods).map(([name, m]) => h("tr", {},
          h("td", { class: "id" }, name, h("div", { class: "text" }, `${m.seconds.toFixed(2)}초`)),
          h("td", {}, badge(m.answers.dept, label ? (m.answers.dept === label.dept ? "go" : "danger") : "out"), probs(m.judgment.dept)),
          h("td", {}, badge(`긴급 ${m.answers.urgent ? "예" : "아니오"}`, "out"),
            typeof m.judgment.urgent === "number" ? h("div", { class: "meters" }, meter("긴급 확률", m.judgment.urgent, { ticks: [0.5] })) : null,
            badge(`불만도 ${m.answers.frustration}`, "out")))))));
  }));
  allBtn.addEventListener("click", () => runBusy(allBtn, status, "30건 × 4방법 판정 중(약 40초)", async () => {
    const s = await api("/api/local-judges/eval", {});
    out.replaceChildren(
      h("p", { class: "text" }, `긴급을 매번 "아니오"로 답하면 ${s.always_not_urgent}/${s.n}.`),
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "방법"), h("th", {}, "정답 수"), h("th", {}, "긴급 AUC · 시간"))),
        h("tbody", {}, Object.entries(s.summary).map(([name, m]) => h("tr", {},
          h("td", { class: "id" }, name),
          h("td", {}, `팀 ${m.dept}/${s.n} · 긴급 ${m.urgent}/${s.n} · 불만도 ${m.frustration}/${s.n}`),
          h("td", {}, m.urgent_auc == null ? "AUC 없음(확률 없음)" : `AUC ${m.urgent_auc.toFixed(2)}`,
            h("div", { class: "text" }, `문의당 ${m.seconds.toFixed(2)}초`)))))));
  }));

  root.append(h("section", { class: "run" },
    h("label", { class: "field" }, "예시 문의", pick),
    h("label", { class: "field" }, "문의", text),
    h("div", { class: "row" }, oneBtn, allBtn, status),
    h("p", { class: "text" }, "d3-flash는 요청 1회에 질문 3개, LLM 확률 읽기는 질문마다 1회(첫 답 토큰의 logprob), LLM JSON은 1회, 나이브 베이즈는 나머지 문의의 라벨로 학습한다."),
    out));
}
