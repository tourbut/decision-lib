// code-judge: behaviour search over this repo's samples, and the checklist review of a diff.
import { api, badge, h, meter, runBusy } from "../common.js";


let LABEL = {};  // checklist key -> Korean name, from /setup

function checklist(r, flagAt) {
  return h("div", { class: "meters" }, Object.entries(r.scores).map(([k, v]) =>
    meter(LABEL[k], v, { ticks: [flagAt], over: v >= flagAt })));
}

function flags(r) {
  return r.flags.length ? r.flags.map((f) => badge(LABEL[f], "danger")) : badge("표시 없음", "go");
}

export async function codeJudgeView(root) {
  const setup = await api("/api/code-judge/setup");
  LABEL = setup.labels;

  // Search
  const question = h("input", { type: "text", value: setup.questions[0].q });
  const searchBtn = h("button", { class: "primary" }, "코드 찾기");
  const searchStatus = h("p", { class: "status", role: "status" });
  const searchOut = h("div");
  searchBtn.addEventListener("click", () => runBusy(searchBtn, searchStatus, "폴더 → 선언 순서로 판정 중", async () => {
    const r = await api("/api/code-judge/search", { question: question.value });
    const known = setup.questions.find((q) => q.q === question.value);
    searchOut.replaceChildren(
      h("p", { class: "text" }, `고른 폴더: ${r.folders.join(", ")} · 키워드 검색 1위: ${r.keyword[0] ?? "없음"}`),
      known ? h("p", { class: "text" }, `라벨: ${known.answers.join(" 또는 ")}`) : "",
      h("table", { class: "results" }, h("tbody", {}, r.results.map((x) => h("tr", {},
        h("td", { class: "id" }, `${x.path}:${x.line}`, h("div", { class: "text" }, x.id.split(":")[1]),
          known?.answers.includes(x.id) ? badge("정답", "go") : null),
        h("td", {}, h("div", { class: "meters" }, meter("확률", x.probability)),
          h("pre", { class: "answer" }, x.excerpt)))))));
  }));
  question.addEventListener("keydown", (e) => { if (e.key === "Enter") searchBtn.click(); });

  // Review
  const pick = h("select", { "aria-label": "예시 diff" },
    setup.diffs.map((d, i) => h("option", { value: i }, `${d.id} (${d.defects.length ? d.defects.map((x) => LABEL[x]).join(", ") : "깨끗함"})`)));
  const diff = h("textarea", { rows: 10, "aria-label": "diff", class: "code" });
  const load = () => { diff.value = setup.diffs[pick.value].diff; };
  pick.addEventListener("change", load);
  load();
  const reviewBtn = h("button", { class: "primary" }, "체크리스트 판정");
  const evalBtn = h("button", { class: "quiet" }, `diff ${setup.diffs.length}개 전부`);
  const reviewStatus = h("p", { class: "status", role: "status" });
  const reviewOut = h("div");
  reviewBtn.addEventListener("click", () => runBusy(reviewBtn, reviewStatus, "판정 중", async () => {
    const r = await api("/api/code-judge/review", { diff: diff.value });
    reviewOut.replaceChildren(h("table", { class: "results" }, h("tbody", {}, h("tr", {},
      h("td", { class: "id" }, flags(r), h("div", { class: "text" }, `조각 ${r.hunks}개`)), h("td", {}, checklist(r, setup.flag_at))))));
  }));
  evalBtn.addEventListener("click", () => runBusy(evalBtn, reviewStatus, "12개 판정 중", async () => {
    const { rows } = await api("/api/code-judge/review/eval", {});
    const planted = rows.reduce((n, r) => n + r.defects.length, 0);
    const caught = rows.reduce((n, r) => n + r.defects.filter((d) => r.flags.includes(d)).length, 0);
    const extra = rows.reduce((n, r) => n + r.flags.filter((f) => !r.defects.includes(f)).length, 0);
    reviewOut.replaceChildren(
      h("p", {}, `심은 결함 ${caught}/${planted} 탐지, 잘못 표시 ${extra}건.`),
      h("table", { class: "results" }, h("tbody", {}, rows.map((r) => h("tr", {},
        h("td", { class: "id" }, r.id, h("div", { class: "text" }, `심은 결함: ${r.defects.map((d) => LABEL[d]).join(", ") || "없음"}`)),
        h("td", {}, flags(r)), h("td", {}, checklist(r, setup.flag_at)))))));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "동작으로 코드 찾기"),
      h("label", { class: "field" }, "질문", question),
      h("div", { class: "row examples" }, "예시:",
        [0, 9, 15, 17].map((i) => h("button", { onclick: () => { question.value = setup.questions[i].q; searchBtn.click(); } },
          setup.questions[i].q))),
      h("div", { class: "row" }, searchBtn, searchStatus),
      h("p", { class: "text" }, `이 레포 samples/의 폴더 ${setup.folders}개, 선언 ${setup.decls}개를 실행할 때마다 ast로 색인한다.`),
      searchOut),
    h("section", { class: "run" },
      h("h3", {}, "체크리스트 리뷰"),
      h("label", { class: "field" }, "예시 diff", pick),
      h("label", { class: "field" }, "diff", diff),
      h("div", { class: "row" }, reviewBtn, evalBtn, reviewStatus),
      reviewOut));
}
