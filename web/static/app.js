// Sample workbench shell. Each sample's view lives in views/<sample>.js; every
// model-produced or user-entered string goes through h() (textContent), never innerHTML.

import { api, h, renderDiagrams, status } from "./common.js";
import { calibrationView } from "./views/calibration.js";
import { citationView } from "./views/citation.js";
import { completionView } from "./views/completion.js";
import { contextView } from "./views/context.js";
import { discoveryView } from "./views/discovery.js";
import { effortView } from "./views/effort.js";
import { ragView } from "./views/rag.js";
import { rerankView } from "./views/rerank.js";
import { toolGateView } from "./views/toolgate.js";

const $ = (sel) => document.querySelector(sel);

// --- Shell ---------------------------------------------------------------------------

const VIEWS = {
  "discovery-review": discoveryView,
  "rag-passage-filter": ragView,
  "tool-call-gate": toolGateView,
  "citation-check": citationView,
  "decision-calibration": calibrationView,
  "effort-router": effortView,
  "completion-check": completionView,
  "rerank": rerankView,
  "context-gate": contextView,
};

async function show(sample) {
  const main = $("#main");
  for (const b of document.querySelectorAll("#nav button")) b.setAttribute("aria-current", String(b.dataset.id === sample.id));
  const diagrams = h("div", { class: "diagrams" });
  const flow = h("details", { class: "flow" }, h("summary", {}, `처리 흐름 (다이어그램 ${sample.diagrams.length}개)`), diagrams);
  flow.addEventListener("toggle", () => {
    if (flow.open && !diagrams.childElementCount) renderDiagrams(diagrams, sample.diagrams);
  });
  const body = h("div");
  main.replaceChildren(h("header", {}, h("h2", {}, sample.title), h("p", {}, sample.summary)), flow, body);
  history.replaceState(null, "", `#${sample.id}`);
  try {
    await VIEWS[sample.id](body);
  } catch (e) {
    body.append(h("p", { class: "status error" }, e.message));
  }
}

async function boot() {
  try {
    const [samples, models] = await Promise.all([api("/api/samples"), api("/api/models")]);
    $("#models").replaceChildren(`판정: ${models.decision}`, h("br"), `생성: ${models.llm || "설정 안 됨"}`);
    $("#nav").replaceChildren(...samples.map((s) =>
      h("button", { "data-id": s.id, onclick: () => show(s) }, s.id, h("small", {}, s.summary))));
    show(samples.find((s) => `#${s.id}` === location.hash) ?? samples[0]);
  } catch (e) {
    status($("#boot"), `서버에 연결하지 못했다: ${e.message}`, true);
  }
}

boot();
