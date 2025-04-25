<h2>🎯 사용 목적</h2>

기술 | 역할 | 요약
-- | -- | --
LangChain | 기본 추론 체인 구성 | LLM 기반 질문/답변 생성 흐름을 정의함
Retrieval 구조 | 유사 질문 검색 | 벡터DB를 통한 context 보강용 검색 수행
LangGraph | 조건 기반 흐름 제어 | 난이도, 키워드 포함 여부에 따라 체인 분기

---

<h2>📌 LangChain 기반 추론 구조</h2>
<h3>✔️ 사용 이유</h3>
<ul>
<li>LLM을 통한 텍스트 생성 흐름을 프롬프트 단위로 명확히 분리하고, 재사용 가능한 구조로 구성 가능</li>
<li>체인 단위로 구성하여, 질문 생성과 답변 생성을 각각 독립적으로 설계할 수 있음</li>
</ul>
<h3>✔️구성 체인 종류</h3>

체인 유형 | 사용 목적 | 설명
-- | -- | --
LLMChain | 질문/답변 생성 | 프롬프트 기반 질문 생성 / 답변 생성에 사용
Retrievr | 유사 질문 검색 | 벡터화된 TIL을 Qdrant에서 유사 질문 검색에 활용


## 📌 체인 정의 코드 예시

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
question_chain = LLMChain(llm=Mistral-7B, prompt=question_prompt)
answer_chain = LLMChain(llm=Mistral-7B, prompt=answer_prompt)

# 검색기 구성 (Qdrant)
retriever = QdrantVectorStore(...).as_retriever()
results = retriever.similarity_search(til, k=3)
```

<h2>📌 LangChain 내 사용 도구 및 외부 리소스</h2>

단계 | 설명 | 사용 도구
-- | -- | --
TIL → 임베딩 | BGE-m3 기반 벡터화 | OllamaEmbeddings + RunnableMap
유사 질문 검색 | Qdrant에서 top-k 검색 | QdrantVectorStore.as_retriever()
질문 생성 | 유사 질문 및 TIL 기반 생성 | PromptTemplate + LLMChain
답변 생성 | 생성된 질문 기반 응답 | PromptTemplate + LLMChain
응답 구성 | JSON 구조화 및 변환 | RunnableMap or 커스텀 처리


<blockquote>
<p>면접 질문 데이터는 GitHub, 블로그, 오픈 데이터셋 기반으로 사전 수집 후 Qdrant에 저장됨</p>
</blockquote>

<hr>

<h2>🧩 LangGraph 도입 필요성 및 실제 적용 방식</h2>
<p>🎯 문제 상황</p>

시나리오 | 문제점
-- | --
유사 질문이 없는 경우 | SequentialChain은 조건 분기가 어려워 fallback 처리가 불가능
조건별 프롬프트 사용 | LLMChain만으로는 조건 분기를 코드 외부에서 처리해야 함
기술 키워드 포함 시 분기 | 전용 체인을 구성하기 어렵고 로직이 분산됨

<p>🎯 LangGraph를 통한 해결</p>

LangGraph 기능 | 도입 이유
-- | --
StateGraph | 유사 질문이 없어 검색 실패 시 fallback 분기 처리
DAG 기반 설계 | 질문 생성 → 답변 생성 → 요약 등 다단계 추론 표현 가능
조건 노드 (e.g. add_conditional_edges()) | 질문 난이도/유사도/키워드 조건 별 프롬프트 분기 명시화


## 🧩 LangGraph 흐름 예시 코드

```python
from langgraph.graph import StateGraph

graph = StateGraph()

# 노드 선언
graph.add_node("embedding", run_embedding) # TIL 벡터화
graph.add_node("search", search_qdrant) # 유사 질문 검색
graph.add_node("route", route_by_score) # 유사도 점수나 조건에 따라 흐름 판단
graph.add_node("fallback_generation", fallback_chain) # 유사 질문이 없을 경우 대체 체인
graph.add_node("contextual_generation", contextual_chain) # 유사 질문 있을 경우 체인
graph.add_node("answer_generation", answer_chain) # 답변 생성 체인
graph.add_node("format", format_output) # 응답 포멧

# 조건 분기
graph.add_conditional_edges("route", {
    "contextual_generation": "contextual_generation",
    "fallback_generation": "fallback_generation"
})

# 기본 연결
graph.set_entry_point("embedding")
graph.add_edge("embedding", "search")
graph.add_edge("search", "route")
# 유사질문이 있든 없든 질문 생성이 끝나면 답변 생성으로 넘어감
graph.add_edge("contextual_generation", "answer_generation")
graph.add_edge("fallback_generation", "answer_generation")
graph.add_edge("answer_generation", "format")
```


## 🧩 LangGraph를 활용한 조건 분기 구조

### 1. 난이도 == '상' → 고난이도 질문 체인 분기

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

사용자의 TIL 내에 사전에 정의된 기술 키워드 리스트 중 하나가 포함되어 있다면

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

<h3>분기 구조 요약표</h3>

조건 | 처리 방식
-- | --
난이도 == '상' | → 고난이도 질문 전용 체인으로 분기 (프롬프트 및 기대 응답 달라짐)
Qdrant 유사 질문 없음 또는 유사도 < 0.75 | → fallback 체인 (검색 없이 TIL만 기반으로 질문 생성)
TIL 내 특정 키워드 포함 | → 기술 전용 질문 프롬프트 체인으로 분기


---


## 📌 전체 AI 추론 흐름도

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



