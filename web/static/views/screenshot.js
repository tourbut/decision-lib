// screenshot-check: judge a labelled page (by screen or by text) or an uploaded screenshot; measure all pages.
import { api, badge, h, meter, runBusy } from "../common.js";


const LABEL = { legit: ["legit 정상", "go"], phishing: ["phishing 사칭", "danger"], other: ["other 해당 없음", "out"], unknown: ["판정 실패", "hold"] };

function labelBadge(label) {
  const [text, tone] = LABEL[label];
  return badge(text, tone);
}

function verdictMeters(v, brands) {
  const s = v.scores;
  if (!s || !Object.keys(s).length) return h("span", { class: "text" }, v.reason);
  return h("div", { class: "meters" },
    meter("비밀번호 입력", s.password_form, { ticks: [0.5], over: s.password_form >= 0.5 }),
    [...brands, "none"].map((b) => meter(b, s[`brand_${b}`], { over: v.brand === b })));
}

function verdictCell(v) {
  return h("td", {}, labelBadge(v.label), h("div", { class: "text" }, v.reason), h("div", { class: "text" }, `호스트 ${v.host}`));
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = () => reject(new Error("파일을 읽지 못했다."));
    reader.readAsDataURL(file);
  });
}

export async function screenshotView(root) {
  const setup = await api("/api/screenshot-check/setup");
  const brands = Object.keys(setup.brands);

  const pick = h("select", { "aria-label": "예시 페이지" },
    setup.pages.map((p) => h("option", { value: p.id }, `[${p.label}] ${p.url}`)));
  const url = h("input", { type: "text", "aria-label": "URL" });
  const upload = h("input", { type: "file", accept: "image/png,image/jpeg", "aria-label": "직접 올릴 화면 캡처" });
  const preview = h("img", { class: "shot", alt: "판정할 화면 캡처" });
  const textBox = h("p", { class: "text" });
  const imageBtn = h("button", { class: "primary" }, "화면으로 판정");
  const textBtn = h("button", { class: "quiet" }, "텍스트로만 판정");
  const oneStatus = h("p", { class: "status", role: "status" });
  const oneOut = h("div");
  function load(id) {
    const p = setup.pages.find((x) => x.id === id);
    url.value = p.url;
    upload.value = "";
    preview.src = `/api/screenshot-check/shot/${p.id}`;
    textBox.textContent = `추출 텍스트: ${p.text}`;
  }
  pick.addEventListener("change", () => load(pick.value));
  upload.addEventListener("change", () => {
    if (!upload.files[0]) return;
    preview.src = URL.createObjectURL(upload.files[0]);
    textBox.textContent = "직접 올린 화면에는 추출 텍스트가 없다. '텍스트로만 판정'은 위 예시 페이지의 텍스트를 쓴다.";
  });
  load(setup.pages[0].id);

  async function judge(mode) {
    const body = { url: url.value, page_id: pick.value, mode };
    if (mode === "image" && upload.files[0]) body.image_base64 = await readFile(upload.files[0]);
    const v = await api("/api/screenshot-check/check", body);
    oneOut.replaceChildren(h("table", { class: "results" }, h("tbody", {}, h("tr", {},
      verdictCell(v), h("td", {}, verdictMeters(v, brands))))));
  }
  imageBtn.addEventListener("click", () => runBusy(imageBtn, oneStatus, "화면을 판정하는 중", () => judge("image")));
  textBtn.addEventListener("click", () => runBusy(textBtn, oneStatus, "텍스트를 판정하는 중", () => judge("text")));

  const evalBtn = h("button", { class: "primary" }, `${setup.pages.length}페이지 측정 (화면·텍스트)`);
  const evalStatus = h("p", { class: "status", role: "status" });
  const evalOut = h("div");
  evalBtn.addEventListener("click", () => runBusy(evalBtn, evalStatus, "판정 중 (약 12초)", async () => {
    const { rows } = await api("/api/screenshot-check/eval", {});
    const hits = (mode) => rows.filter((r) => r[mode].label === r.label).length;
    evalOut.replaceChildren(
      h("p", {}, `라벨 일치: 화면 ${hits("image")}/${rows.length}, 텍스트만 ${hits("text")}/${rows.length}.`),
      h("table", { class: "results" },
        h("thead", {}, h("tr", {}, h("th", {}, "페이지"), h("th", {}, "화면으로"), h("th", {}, "텍스트로만"))),
        h("tbody", {}, rows.map((r) => h("tr", {},
          h("td", { class: "id" }, r.url, h("div", { class: "text" }, `라벨: ${r.label}`)),
          verdictCell(r.image), verdictCell(r.text))))));
  }));

  root.append(
    h("section", { class: "run" },
      h("h3", {}, "페이지 하나 판정"),
      h("label", { class: "field" }, "예시 페이지", pick),
      h("label", { class: "field" }, "URL (바꾸면 같은 화면을 다른 주소로 판정한다)", url),
      h("label", { class: "field" }, "또는 직접 올린 화면 캡처 (PNG·JPEG, 3MB 이하)", upload),
      preview, textBox,
      h("div", { class: "row" }, imageBtn, textBtn, oneStatus),
      oneOut),
    h("section", { class: "run" },
      h("h3", {}, "라벨 측정"),
      h("p", { class: "text" }, "가상 회사·도메인으로 만든 페이지다. 사칭 8개 중 4개는 브랜드를 로고 그림으로만 넣어 텍스트에는 이름이 없다. 모델은 URL을 보지 않고, 공식 호스트 여부는 코드가 등록 목록과 비교한다."),
      h("div", { class: "row" }, evalBtn, evalStatus),
      evalOut));
}
