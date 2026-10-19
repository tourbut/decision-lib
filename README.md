# decision-lib

decision 모델을 쓰는 샘플 프로젝트 모음이다. 샘플은 서로 독립적이며 `samples/<이름>/`에 각자 uv 프로젝트로 둔다.

decision 모델은 텍스트를 생성하지 않는다. 상태(state)와 질문을 받아 질문마다 타입이 있는 답과 확률을 돌려준다. 그래서 라우팅·검증 같은 판단을 일반 코드가 바로 쓸 수 있다. 샘플은 TypeSafe Jev 대신 로컬 `d3-flash`를 쓴다.

## 샘플

| 샘플 | 내용 | 참고 |
|---|---|---|
| [discovery-review](samples/discovery-review/README.md) | LangGraph로 만든 소송 디스커버리 문서 검토 파이프라인. 페이지마다 관련성·특권·개인정보를 판정해 제출·보류·레드랙션·변호사 검토로 보낸다 | [Building prod with Jev and LangGraph](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph) |
| [rag-passage-filter](samples/rag-passage-filter/README.md) | RAG 검색 문단을 생성 전에 분류한다. 관련성·근거·전제 충돌·프롬프트 인젝션을 판정해 채택 근거·충돌 근거·제외로 나눈다 | [TypeSafe cookbook](https://docs.typesafe.ai/cookbooks/classifying_rag_passages), #3 |

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

1. `samples/<이름>/`에 `pyproject.toml`(uv, `package = false`)과 `README.md`를 만든다.
2. 네트워크 없이 도는 테스트를 두고, 실제 모델 실행은 `demo.py` 같은 별도 스크립트로 분리한다.
3. 위 샘플 표에 한 줄을 추가한다.
4. 테스트 명령을 `.fullops-squad/lint/lint.json`의 `commands`에 등록한다.
