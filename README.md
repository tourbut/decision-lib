# decision-lib

decision 모델을 쓰는 샘플 프로젝트 모음이다. 샘플은 서로 독립적이며 `samples/<이름>/`에 각자 uv 프로젝트로 둔다.

decision 모델은 텍스트를 생성하지 않는다. 상태(state)와 질문을 받아 질문마다 타입이 있는 답과 확률을 돌려준다. 그래서 라우팅·검증 같은 판단을 일반 코드가 바로 쓸 수 있다. 샘플은 TypeSafe Jev 대신 로컬 `d3-flash`를 쓴다.

## 샘플

| 샘플 | 내용 | 참고 |
|---|---|---|
| [discovery-review](samples/discovery-review/README.md) | LangGraph로 만든 소송 디스커버리 문서 검토 파이프라인. 페이지마다 관련성·특권·개인정보를 판정해 제출·보류·레드랙션·변호사 검토로 보낸다 | [Building prod with Jev and LangGraph](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph) |
| [rag-passage-filter](samples/rag-passage-filter/README.md) | RAG 검색 문단을 생성 전에 분류한다. 관련성·근거·전제 충돌·프롬프트 인젝션을 판정해 채택 근거·충돌 근거·제외로 나눈다 | [TypeSafe cookbook](https://docs.typesafe.ai/cookbooks/classifying_rag_passages), #3 |
| [tool-call-gate](samples/tool-call-gate/README.md) | 에이전트가 도구를 실행하기 직전에 차단 규칙과 판정으로 실행·사람 확인·차단을 정한다. LangChain 미들웨어로 로컬 LLM 에이전트에 붙이고, 라벨 50건으로 규칙만 쓸 때와 비교한다 | [Building a harness with Jev](https://www.langchain.com/blog/building-a-harness-with-jev), #7 #6 #27 #38 |
| [citation-check](samples/citation-check/README.md) | LLM 답변의 인용을 출처와 대조한다. 인용문 실재는 문자열로, 주장과 문맥의 관계는 Choice로 판정해 verified·contradicted·unsupported·fabricated로 나누고 확신도 0.8 미만은 사람 검토로 보낸다 | [TypeSafe cookbook: citation check](https://docs.typesafe.ai/cookbooks/citation_check), #4 |
| [decision-calibration](samples/decision-calibration/README.md) | 판정 확률을 믿어도 되는지 잰다. NSMC 공개 리뷰로 Choice·Noul의 정확도·ECE·Brier·사람 검토 비율을, 문의 라우팅으로 선택지 순서 편향과 L0 보정을 비교한다 | [Raschka](https://magazine.sebastianraschka.com/p/classifier-history-and-jev), [AnyJev](https://github.com/nokia-applied-research/AnyJev), #15 #24 |
| [effort-router](samples/effort-router/README.md) | 턴마다 추론 끔(fast)·추론 켬(think)·이관(handoff)을 정하는 LangChain 미들웨어. 안전 조건은 이관, 불확실하면 think, 답이 잘리면 한 단계 올린다. 항상 fast·항상 think와 정답·토큰을 비교한다 | [jev-effort-router](https://hermes-agent.nousresearch.com/docs/plugins/jev-effort-router), [effortless-hermes](https://hermes-agent.nousresearch.com/docs/plugins/effortless-hermes), #7 #21 #29 #30 |
| [completion-check](samples/completion-check/README.md) | 에이전트가 "다 했다"고 할 때 요구사항·테스트·사람 개입 필요를 판정해 pass·steer·halt로 나눈다. 테스트 실패와 시도 상한은 코드가 정하고, LangChain after_model 미들웨어로 덜 된 답을 되돌린다 | [Foreman](https://github.com/thruwire/foreman), Hermes pre_verify, #10 #37 |
| [rerank](samples/rerank/README.md) | BM25 후보를 d3-flash Score 루브릭(10단계 관련도, 3단계 근거)으로 다시 채점한다. 공개 벤치마크 SciFact로 nDCG@10을 재고 BM25와 RRF로 합친 순서도 비교한다 | [LambdaDB native reranking](https://lambdadb.ai/blog/native-reranking-with-jev), [jev-search](https://github.com/superagents-lab/jev-search), #5 #17 |

## 웹에서 실행

`web/`은 샘플을 브라우저에서 실행하는 화면이다. 판정 확률과 분기 임계값, 처리 흐름 다이어그램을 함께 보여 준다. 자세한 내용은 [web/README.md](web/README.md)에 있다.

```bash
cd web && uv sync && uv run uvicorn app:app --port 8300   # http://127.0.0.1:8300
```

## 모델

| 모델 | 용도 | 위치 |
|---|---|---|
| `d3-flash` | decision 모델. `POST /v1/systemone`, `GET /v1/models`, `GET /health` | 로컬 docker `dgx-decision-d3-flash`, `127.0.0.1:30010` |
| 로컬 LLM | 생성이 필요한 단계에만 쓴다(예: 레드랙션). OpenAI 호환 API | `.env`의 `LOCAL_LLM_URL` |

d3-flash의 요청·응답 형식은 TypeSafe API와 같다. 그래서 `langchain-typesafe`의 `TypeSafeClassifier`에 `base_url`만 지정해 쓸 수 있다. 서버는 요청의 `model` 값을 무시한다. 질문 타입은 `choice`(선택지별 확률), `score`(순서 있는 단계의 기댓값), `noul`(예/아니오 확률)이다.

```bash
curl -s http://127.0.0.1:30010/v1/systemone -H 'Content-Type: application/json' -d '{
  "model": "d3-flash",
  "state": "The order arrived damaged. The customer has a receipt.",
  "questions": {"receipt": {"type": "noul", "instructions": "Does the customer have a receipt?"}}
}'
```

## 설정

레포 루트 `.env`에 모델 접속 정보를 둔다. `.env`는 커밋하지 않는다. 샘플은 `python-dotenv`의 `find_dotenv()`로 이 파일을 찾는다.

```bash
DECISION_BASE_URL=http://127.0.0.1:30010
DECISION_MODEL=d3-flash
DECISION_API_KEY=            # 서버에 키를 설정했을 때만
LOCAL_LLM_URL=http://<host>:<port>/v1
LOCAL_LLM_MODEL=<model>
```

워크트리에서 작업할 때는 main 체크아웃의 `.env`를 심볼릭 링크로 연결한다.

## 샘플 추가

1. `samples/<이름>/`에 `pyproject.toml`(uv, `package = false`)과 `README.md`를 만든다. README는 처리 흐름을 mermaid 다이어그램으로 설명한다(판정 지점·임계값·분기 결과 포함).
2. 네트워크 없이 도는 테스트를 두고, 실제 모델 실행은 `demo.py` 같은 별도 스크립트로 분리한다.
3. 위 샘플 표에 한 줄을 추가한다.
4. `web/`에 어댑터와 화면을 추가한다([web/README.md](web/README.md)의 샘플 추가 절).
5. 테스트 명령을 `.fullops-squad/lint/lint.json`의 `commands`에 등록한다.
