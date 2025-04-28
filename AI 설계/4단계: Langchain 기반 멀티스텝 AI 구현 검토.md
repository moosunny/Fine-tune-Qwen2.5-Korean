## 🎯  Langchain사용 목적

| 기술 | 역할 | 요약 |
| --- | --- | --- |
| **LangChain** | 기본 추론 체인 구성 | LLM 기반 질문/답변 생성 흐름을 정의함 |
| **Retrieval 구조** | 유사 질문 검색 | Qdrant를 통한 context 보강용 검색 수행 |
| **LangGraph** | 조건 기반 흐름 제어 | fallback, 난이도, 키워드 포함 여부에 따라 체인 분기 |

## 📌 LangChain 기반 추론 구조

### ✔️ 사용 이유

- LLM을 통한 텍스트 생성 흐름을 **프롬프트 단위로 명확히 분리**하고, 재사용 가능한 구조로 구성 가능
- 체인 단위로 구성하여, 질문 생성과 답변 생성을 각각 독립적으로 설계할 수 있음

### ✔️구성 체인 종류

| 체인 유형 | 사용 목적 | 설명 |
| --- | --- | --- |
| `LLMChain` | 질문/답변 생성 | 프롬프트 기반 질문 생성 / 답변 생성에 사용 |
| `RetrievalChain` | TIL → 유사 질문 검색 | 벡터화된 TIL을 Qdrant에서 유사 질문 검색에 활용 |

---

## 1. `/til` : Commit 기반 TIL 생성 Langgraph 개요

![Image](https://github.com/user-attachments/assets/4eb94a58-3cb5-4815-b66a-80b4012ce4a3)

### 1. 체인의 각 단계와 작동 방식

- 초기 입력 데이터를 받아들이는 **start 단계**
- 입력 데이터(`files`)를 다수의 작업으로 분기하는 **fork 단계(MVP 단계에서는 최대 5개 커밋 허용)**
- 각 파일별로 기술 스택, 기능, 책임을 요약하는 **code_summary_node 단계**
- 각 파일별 변경사항을 분석하고 요약하는 **patch_summary_node 단계**
- 모든 파일의 요약 결과를 통합해 TIL 초안을 생성하는 **til_draft_node 단계**
- 초안을 리뷰하고 수정하여 품질을 개선하는 **til_feedback_node 단계**
- 최종 결과를 반환하고 체인을 종료하는 **end 단계**

---

### 2. vLLM 기반 비동기 엔진 도입을 통한 동시 요청 수용

- **도입 배경 및 아키텍처 적합성**
    - 입력 파일이 여러 개인 경우(fork) 각 파일마다 동시에 요약, 변경 분석이 필요한 **멀티 인퍼런스 체계**
    - 코드 요약 → 패치 요약 → TIL 작성까지 모든 단계가 LLM 호출로 구성된 **다단계 추론 파이프라인**
    - 각 단계에서 요청이 중첩되고 증가하는 구조를 감당하기 위한 **고성능 비동기 처리 필요성**
    - vLLM의 메모리 효율성과 동시 요청 최적화 기능이 본 아키텍처에 가장 부합하는 **엔진 선택 이유**
    
- **vLLM 초기화 및 성능 관련 핵심 지표(Gemma3-12b-it-GPTQ)**
    
    
    | 항목 | 수치 및 결과 | 의미 |
    | --- | --- | --- |
    | 모델 로딩 VRAM 사용량 | 8.42 GiB | 전체 24GiB 중 35%만 사용 |
    | Encoder cache 예산 | 8,192 tokens | 동시 요청 토큰 버퍼 확보 |
    | KV 캐시 메모리 크기 | 22,224 tokens | 추가 요청 수용 여유 공간 |
    | 4096 tokens 기준 동시성 | 5.43배 | 한 번에 약 5건 이상의 대형 요청 가능 |
    | Torch.compile 최적화 시간 | 25.15초 | 최초 1회 컴파일 후 캐시 재사용 |
    | 전체 엔진 워밍업 시간 | 102초 | 초기 준비 완료 후 빠른 응답 가능 |

- L4 환경(GPU 제한)에서의 도입 당위성
    - 24GB VRAM 내에서 추론, 캐시, 그래프 컴파일까지 모두 수용하는 **메모리 최적화 완료**
    - 입력 파일 수에 따라 요약 요청이 5배 이상 동시 증가해도 감당 가능한 **동시성 보장 구조**
    - 초기 torch.compile을 통해 추론 경로를 고정하여 매 요청시 오버헤드가 없는 **추론 속도 최적화**
    - 추가 메모리 사용 없이 다수 요청을 흡수할 수 있는 kv-cache 압축 및 관리 구조를 갖춘 **엔진 설계**
    - 결과적으로 L4 GPU 하나만으로 실서비스 가능성을 확보하는 **비용 대비 성능 최적 선택**

---

### 3. Langgraph 노드별 프롬프트 예시

| 코드 영역 | 핵심 목적 |
| --- | --- |
| StateType 정의 | 전체 체인 입력/출력 데이터 구조 관리 |
| make_code_summary_prompt | 소스코드 요약용 프롬프트 생성 |
| make_patch_summary_prompt | 변경 이력 요약용 프롬프트 생성 |
| til_draft_prompt | TIL 초안 작성용 프롬프트 생성 |
| til_feedback_prompt | TIL 초안 개선용 Self-Feedback 프롬프트 생성 |

### TypedDict State 정의

- 전체 워크플로우에서 주고받을 데이터 타입을 명시한 **State 객체 정의**
- 파일 리스트, 요약 결과, TIL 초안 및 최종본까지 모든 중간 상태를 관리하는 **State 관리 구조**
- code_summary, patch_summary 항목은 다수 노드 결과를 병합하기 위해 **merge_dicts 어노테이션 적용**

```jsx
class PatchDict(TypedDict):    
    commit_message: str
    patch: str

class FileDict(TypedDict):
    filepath: str
    latest_code: str
    patches: List[PatchDict]

class StateType(TypedDict, total=False):
    username: str
    date: str
    repo: str
    files: List[FileDict]
    code_summary: Annotated[Dict[str, str], merge_dicts]  # 노드별 코드 요약(dict)
    patch_summary: Annotated[Dict[str, str], merge_dicts] # 노드별 코드 변경사항 요약(dict) 
    til_draft: str  # TIL 초안
    til_final: str  # 개선된 최종 TIL
```

### 코드 요약 프롬프트

- 각 소스파일을 분석하여 사용 기술, 주요 기능, 프로젝트 책임 역할을 추출하는 **코드 요약 프롬프트 생성 함수**
- 요청한 결과를 깔끔한 개조식 문장으로 정리하게 만드는 **프롬프트 지침 포함**
- 입력 데이터로 파일 경로와 코드 전문을 받아 프롬프트로 구성하는 **파일 기반 입력 구조**

```python
# code summary 함수
def make_code_summary_prompt(file: dict) -> str:
    filepath = file["filepath"]
    latest_code = file["latest_code"]

    prompt = f"""
다음은 소프트웨어 프로젝트의 하나의 소스코드 파일입니다.
주어진 코드를 분석하여 핵심 내용을 간단한 개조식 문장으로 요약해 주세요.

요약 항목:
- 사용 기술 스택 (언어, 프레임워크)
- 주요 기능
- 프로젝트 내 기능

요약은 다음처럼 개조식으로 작성해 주세요:

예시:
- 언어: Python, 프레임워크: FastAPI
- 기능: 사용자 인증 처리
- 기능: API 서버 인증 모듈 담당

[파일 경로]
{filepath}

[코드]
{latest_code}
"""
    return prompt
```

### 코드 변경사항 요약 프롬프트

- 소스코드 변경사항(patch)와 기존 코드 요약을 기반으로 변경 목적과 수정사항을 추출하는 **변경 요약 프롬프트 생성 함수**
- 코드 변경 이유, 핵심 수정사항, 변경 흐름까지 요약하여 기록하는 **변경 이력 분석 목적**
- 출력 형식을 명시하고, 일관된 개조식 문장 형태로 결과를 유도하는 **프롬프트 가이드라인 포함**

```python
# patch summary 함수
def make_patch_summary_prompt(code_summary: str, patch_section: str) -> str:
    prompt = f"""
다음은 하나의 소스코드 파일에 대한 코드 요약과 변경 이력입니다.
변경 이력(patch)을 바탕으로 변경 목적과 주요 수정사항을 간단한 개조식 문장으로 요약해 주세요.

[코드 요약]
{code_summary}

[변경 이력]
{patch_section}

요약 항목:
- 주요 변경 목적
- 핵심 수정사항 요약
- 변경 흐름 요약 (필요 시)

요약은 다음처럼 개조식으로 작성해 주세요:

예시:
- 기능 추가: OAuth 인증 모듈 도입
- 버그 수정: 로그인 세션 만료 문제 해결
- 구조 개선: Controller 레이어 분리

답변은 한국어로, 개조식 문장으로만 작성하세요.
"""
    return prompt
```

### TIL 초안 작성 프롬프트

- 여러 파일 요약 결과를 통합하여 하나의 TIL 초안을 생성하는 **TIL 작성 프롬프트 생성 함수**
- 작성된 TIL은 사용자 아이디, 날짜, 레포지토리 정보와 함께 JSON 포맷으로 출력하는 **구조화된 데이터 요구**
- TIL 내용은 "오늘 배운 내용, 개념 정리, 활용법, 문제 해결, 회고"까지 포함하는 **학습 일지 작성 기준 적용**

```python
# TIL 초안 생성 프롬프트
def til_draft_prompt(username: str, date: str, repo: str, combined_summary: str) -> str:
    prompt = f"""
다음은 하나 이상의 소스코드 파일에 대한 분석 요약과 변경 이력 분석입니다. 이를 참고하여 마크다운 형식의 TIL을 작성해 주세요.

[코드 + 변경 요약]
{combined_summary}

요구 조건:
- 다음 형식의 JSON으로 작성:
{{
  "user": "{username}",
  "date": "{date}",
  "repo": "{repo}",
  "title": "<{date} 포함 제목>",
  "keywords": ["<핵심 기술 키워드 1~3개>"],
  "content": "<마크다운 형식 TIL>"
}}

TIL 작성 시 반드시 포함할 항목 (개조식):
1. 오늘 배운 내용
2. 개념 정리
3. 해당 개념이 필요한 이유
4. 개념을 활용하는 방법
5. 문제 해결 과정
6. 하루 회고
7. 전체적으로 개조식 문장 구성

TIL 내용은 한국어로 작성하세요.
"""
    return prompt
```

### TIL 초안 피드백 노드 프롬프트

- 작성된 TIL 초안을 받아 자연스럽게 다듬고 구체화하는 **Self-feedback 프롬프트 생성 함수**
- 중복 제거, 표현 명확화, 개조식 통일 등 품질 개선을 위한 구체적 기준을 제시하는 **TIL 품질 개선 지침 포함**
- 결과물은 반드시 **개조식+마크다운 포맷 유지**하도록 요구하며, TIL 본문만 출력하는 **엄격한 출력 포맷 규칙 설정**

```python
# 피드백 루프
def til_feedback_prompt(content: str) -> str:
    """
    TIL 초안을 받아서 개선 지침을 포함한 feedback prompt를 생성합니다.

    Args:
        content (str): 초안 TIL 내용 (마크다운 텍스트)

    Returns:
        str: LLM에게 전달할 최종 프롬프트 텍스트
    """
    feedback_prompt = f"""
다음은 오늘 학습한 내용을 정리한 TIL 초안입니다.

[TIL 초안]
{content}

이 TIL을 다음 기준에 따라 평가하고, 더 구체적이고 일관성 있는 TIL로 개선해 주세요:

✅ 개선 기준:
1. **중복 문장 제거** – 유사하거나 반복되는 문장은 하나로 합쳐 주세요.
2. **표현의 명확성** – 불분명하거나 모호한 표현을 구체적으로 바꿔 주세요.
3. **개조식 통일** – 문장형 서술이 있다면 개조식으로 정리해 주세요.
4. **불필요한 서론 제거** – 지나치게 일반적이거나 반복되는 내용은 생략해 주세요.
5. **자주 사용되는 추상 표현 제거** – "새로운 면모", "실감나게", "꾸준히", "흥미로웠다" 등의 모호한 감정/상태 표현은 구체적인 행동, 성과, 계획으로 바꿔 주세요.
6. **자연스러운 문장 구성** – 한국어 맞춤법 및 어투를 자연스럽게 다듬어 주세요. 문장이 너무 길어지면 줄바꿈으로 구조를 직관적으로 보이게 작성하세요.

✅ 출력 형식:
- 수정된 TIL 전체 (마크다운 형식 유지)

**주의**: 결과는 반드시 한국어로 작성해 주세요. 초안에 대한 피드백 부분은 작성하지 마세요. **TIL 본문만 필요합니다.**
"""
    return feedback_prompt
```

---

### 4. 멀티스텝 체인 도입의 장점 및 서비스 기능 연관성

- 여러 소스 파일을 독립적으로 분석하고 취합하여 전체 요약 정확도를 향상시키는 **복잡한 작업 자동화 기능**
- 중간 요약 단계를 거치면서 정보 손실과 왜곡을 방지하여 생성 품질을 높이는 **답변 정확도 향상 기능**
- 코드 요약, 변경사항 요약, 초안 작성, 피드백 단계를 명확히 분리하여 결과의 일관성을 유지하는 **구조화된 결과 생성 기능**
- 모듈형 설계로 특정 노드만 교체하거나 추가할 수 있어 유연성을 확보하는 **유지보수 및 확장성 향상 기능**
- 입력된 파일의 커밋 변경 내역을 바탕으로 TIL을 자동 생성하는 데 최적화된 **서비스 기능과의 연관성 확보**

---

## 2. `/interveiw` : TIL 기반 면접 질문 생성 Langchain 개요

## **📌** 체인 정의 **코드 예시**

```python
# 질문 프롬프트
question_prompt = PromptTemplate(
    input_variables=["til", "difficulty"],
    template="""
너는 기술 면접관이야. 아래 TIL을 바탕으로 난이도 {difficulty} 수준의 면접 질문을 생성해줘.\nTIL:\n{til}\n질문:
"""
)

# 답변 프롬프트
answer_prompt = PromptTemplate(
    input_variables=["question"],
    template="""
다음 질문에 대한 간단한 모범 답변을 작성해줘:\n{question}\n답변:
"""
)

# 체인 구성
question_chain = LLMChain(llm=llm, prompt=question_prompt)
answer_chain = LLMChain(llm=llm, prompt=answer_prompt)

# 검색기 구성 (Qdrant)
retriever = QdrantVectorStore(...).as_retriever()
results = retriever.similarity_search(til, k=3)
```

## **📌 LangChain 내 사용 도구 및 외부 리소스**

| 단계 | 설명 | 사용 도구 |
| --- | --- | --- |
| TIL → 임베딩 | BGE-m3 기반 벡터화 | `OllamaEmbeddings` + `RunnableMap` |
| 유사 질문 검색 | Qdrant에서 top-k 검색 | `QdrantVectorStore.as_retriever()` |
| 질문 생성 | 유사 질문 및 TIL 기반 생성 | `PromptTemplate` + `LLMChain` |
| 답변 생성 | 생성된 질문 기반 응답 | `PromptTemplate` + `LLMChain` |
| 응답 구성 | JSON 구조화 및 변환 | `RunnableMap` or 커스텀 처리 |

> 면접 질문 데이터는 GitHub, 블로그, 오픈 데이터셋 기반으로 사전 수집 후 Qdrant에 저장됨
> 

---

## **🧩 LangGraph 도입 필요성 및 실제 적용 방식**

🎯 **문제 상황**

| 시나리오 | 문제점 |
| --- | --- |
| 유사 질문이 없는 경우 | `SequentialChain`은 조건 분기가 어려워 fallback 처리가 불가능 |
| 조건별 프롬프트 사용 | `LLMChain`만으로는 조건 분기를 코드 외부에서 처리해야 함 |
| 기술 키워드 포함 시 분기 | 전용 체인을 구성하기 어렵고 로직이 분산됨 |
| 반복 생성 시 상태 유지 | Stateless 구조로 동일 입력에 대한 흐름 유지를 구현하기 어려움 |

🎯 **LangGraph를 통한 해결**

| LangGraph 기능 | 도입 이유 |
| --- | --- |
| `StateGraph` | 유사 질문이 없어 검색 실패 시 fallback 분기 처리 |
| DAG 기반 설계 | 질문 생성 → 답변 생성 → 검수 등 다단계 추론 표현 가능 |
| 조건 노드 
(e.g. `add_conditional_edges()`) | 질문 난이도/유사도/키워드 조건 별 프롬프트 분기 명시화 |

---

## **🧩 LangGraph 흐름 예시 코드**

```python
from langgraph.graph import StateGraph

graph = StateGraph()

# 노드 선언
graph.add_node("embedding", run_embedding)
graph.add_node("search", search_qdrant)
graph.add_node("route", route_by_score)
graph.add_node("fallback_generation", fallback_chain)
graph.add_node("contextual_generation", contextual_chain)
graph.add_node("answer_generation", answer_chain)
graph.add_node("format", format_output)

# 조건 분기
graph.add_conditional_edges("route", {
    "contextual_generation": "contextual_generation",
    "fallback_generation": "fallback_generation"
})

# 기본 연결
graph.set_entry_point("embedding")
graph.add_edge("embedding", "search")
graph.add_edge("search", "route")
graph.add_edge("contextual_generation", "answer_generation")
graph.add_edge("fallback_generation", "answer_generation")
graph.add_edge("answer_generation", "format")
```

---

## 🧩 LangGraph 조건 분기 설계

### 1. **난이도 == '상' → 고난이도 질문 체인 분기**

사용자의 TIL과 함께 입력된 난이도가 '상'일 경우,
→ 기본 체인과는 별도로 고난이도 전용 프롬프트를 사용하는 질문 생성 체인으로 분기됨.

```python
def route_by_difficulty(state):
    difficulty = state["difficulty"]
    
    if difficulty == "상":
        return "advanced_generation"
    elif difficulty == "중":
        return "intermediate_generation"
    else:
        return "basic_generation"
```

### 2. 유사 질문 검색 실패 → `fallback` 분기 필요

사용자의 TIL을 벡터화하고 Qdrant에 top-k 유사도 검색을 요청했을 때, 다양한 상황이 발생할 수 있음:

- 검색된 유사 질문 수가 0개
- 검색 결과가 있더라도 유사도가 0.75 미만으로 낮음

이러한 경우에는 검색된 질문을 기반으로 질문을 생성하면 정확도가 떨어지기 때문에

→ 벡터 검색을 생략하고 TIL 원문만으로 질문을 생성하는 fallback 체인으로 분기함.

```python
def route_by_search_result(state):
    results = state["search_results"]
    max_score = max([r.score for r in results]) if results else 0
    
    if len(results) == 0 or max_score < 0.75:
        return "fallback_generation"
    else:
        return "contextual_generation"
```

### 3. 특정 기술 키워드 포함 시 → 기술 전용 프롬프트 체인 분기

사용자의 TIL 내에 사전에 정의된 기술 키워드 리스트 중 하나가 포함되어 있다면,

→ 일반적인 질문 체인이 아니라, 기술 특화 프롬프트를 사용하는 별도 체인으로 분기.

```python
def route_by_keywords(state):
    til_text = state["til"]
    tech_keywords = ["Docker", "JWT", "TensorFlow", "PyTorch", "Kubernetes"]
    
    if any(keyword.lower() in til_text.lower() for keyword in tech_keywords):
        return "tech_specialized_generation"
    else:
        return "general_generation"
```

### 분기 구조 요약표

| 조건 | 처리 방식 |
| --- | --- |
| **난이도 == '상'** | → 고난이도 질문 전용 체인으로 분기 (프롬프트 및 기대 응답 달라짐) |
| **Qdrant 유사 질문 없음** 또는 **유사도 < 0.75** | → fallback 체인 (검색 없이 TIL만 기반으로 질문 생성) |
| **TIL 내 특정 키워드 포함** | → 기술 전용 질문 프롬프트 체인으로 분기 |

---

## **📌 전체** AI 추론 흐름도

```
┌──────────────────────────────┐
│ 사용자 입력 수신                 │ TIL, 날짜, 난이도
└────────────┬─────────────────┘
             ▼
┌─────────────────────────────┐
│ TIL 전처리 및 벡터 임베딩 생성    │ ← LangChain Runnable
└────────────┬────────────────┘
             ▼
┌─────────────────────────────┐
│ Qdrant 벡터DB에서 유사 질문 검색  │ ← Retriever
│ - Top-k 관련 질문 반환          │
└────────────┬────────────────┘
             ▼
┌────────────────────────────┐
│ 검색 결과 존재 여부 확인         │ ← LangGraph
│ - 관련 질문이 없으면 Fallback   │
└─────┬─────────────┬────────┘
      │             │
      ▼             ▼
┌──────────────┐  ┌───────────────────────┐
│ 유사 질문 있음  │  │ 유사 질문 없음 (Fallback) │
└────┬─────────┘  └─────────────┬─────────┘
     ▼                          ▼
┌──────────────────────────────────┐
│ 면접 질문 생성 (LLM + 프롬프트)        │ ← LangChain LLMChain
│  - 난이도 기반 분기                  │
└─┬──────────┬────────────┬────────┘
  │          │            │
  ▼          ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐
│ 기본    │ │ 중급    │ │ 고급    │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┴──────────┘
              ▼            
┌─────────────────────────────┐
│      질문 기반 답변 생성         │ ← LangChain LLMChain
└────────────┬────────────────┘
             ▼
┌──────────────────────────────────┐
│ 응답 포맷 구성 및 반환                │
│  - {difficulty, question, answer}│
└──────────────────────────────────┘
```
