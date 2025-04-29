<h2> 📌 전체 데이터 흐름</h2>

1. **사용자 질의 입력 (FastAPI)**
    - 입력 데이터: {TIL 텍스트, 제목, 키워드, 난이도("상/중/하")}
2. **텍스트 임베딩 변환 (BGE-M3 임베딩 모델)**
    - 입력된 TIL 텍스트를 1024차원 벡터로 변환
    - 출력: 임베딩 벡터 (float32)
3. **유사 질문 검색 (Qdrant 벡터DB)**
    - 생성된 벡터를 기반으로 기존 면접 질문 데이터셋과 Top-k 유사도 검색
    - 검색 기준: Cosine Similarity (0.75 이상 선별)
4. **검색 결과 재정렬 및 필터링**
    - 난이도, 주제 태그, 최신성 기준으로 결과 스코어 재조정
5. **프롬프트 생성**
    - 검색된 질문 3~5개와 TIL을 기반으로 새로운 지시형 프롬프트 작성
6. **생성 모델 추론 (vLLM + Mistral-7B)**
    - 최종 프롬프트를 모델에 입력하여 새로운 질문 + 답변 생성
7. **응답 반환 (JSON 구조화)**
    - 최종 질문/답변 쌍을 반환, 사용자 요청 ID와 함께 관리

<img width="1172" alt="image" src="https://github.com/user-attachments/assets/d9104cb1-1f26-4fd8-9688-a8fa3be91c17" />

<h2>📌 외부 지식 소스 및 선정 이유</h2>

항목 | 소스명 | 사용 목적 | 선정 이유
-- | -- | -- | --
벡터DB | Qdrant | 빠른 벡터 검색 및 메타데이터 기반 재정렬 | GPU 의존 없이 고성능 검색, 쉬운 API 연동
임베딩 모델 | BGE-M3-small | 텍스트 의미 임베딩 | 다양한 도메인 적응성, 한국어/영어 혼합 대응
생성 모델 | Mistral-7B-Instruct | 질문/답변 생성 | 중간 규모로 속도와 품질 균형, vLLM 최적화 가능

사전 수집된 질문 데이터 </br>

https://github.com/zzsza/Datascience-Interview-Questions?tab=readme-ov-file#%EB%B6%84%EC%84%9D-%EC%9D%BC%EB%B0%98
https://github.com/boost-devs/ai-tech-interview?tab=readme-ov-file

```python
{'question': 'ROC 커브에 대해 설명해주실 수 있으신가요?', 'category': '머신러닝'}
{'question': '여러분이 서버를 100대 가지고 있습니다. 이때 인공신경망보다 Random Forest를 써야하는 이유는 뭘까요?', 'category': '머신러닝'}
{'question': 'K-means의 대표적 의미론적 단점은 무엇인가요? (계산량 많다는것 말고)', 'category': '머신러닝'}
{'question': 'L1, L2 정규화에 대해 설명해주세요', 'category': '머신러닝'}
{'question': '50개의 작은 의사결정 나무는 큰 의사결정 나무보다 괜찮을까요? 왜 그렇게 생각하나요?', 'category': '머신러닝'}
{'question': '스팸 필터에 로지스틱 리그레션을 많이 사용하는 이유는 무엇일까요?', 'category': '머신러닝'}
{'question': 'OLS(ordinary least squre) regression의 공식은 무엇인가요?', 'category': '머신러닝'}
{'question': '딥러닝은 무엇인가요? 딥러닝과 머신러닝의 차이는?', 'category': '딥러닝 일반'}
{'question': '왜 갑자기 딥러닝이 부흥했을까요?', 'category': '딥러닝 일반'}
```

<h2> 📌 검색 및 LLM 통합 방식 구현</h2>

### 임베딩 생성 + 데이터 삽입

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# 모델 로드
model = SentenceTransformer("intfloat/e5-mistral-7b")
vectors = model.encode([q["question"] for q in data])

# Qdrant 연결
client = QdrantClient(host="localhost", port=6333)

# 벡터 컬렉션 생성
client.recreate_collection(
    collection_name="interview-questions",
    vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE)
)

# 데이터 삽입
client.upsert(
    collection_name="interview-questions",
    points=[
        PointStruct(id=i, vector=vectors[i], payload=data[i])
        for i in range(len(data))
    ]
)
```

Prompt 구성 예시

```python
retrieved_questions = retriever.invoke(user_til)
retrieved_str = "\n".join([f"- {q['question']}" for q in retrieved_questions])

prompt = 
f"""
당신은 사용자의 기술 학습 기록을 바탕으로, 기술 면접에 적합한 질문과 답변을 생성하는 AI입니다.

아래 정보를 참고하여,
- 먼저 하나의 면접 질문을 만들고
- 그 다음 해당 질문에 대한 답변을 작성해주세요.

※ 난이도에 따라 질문과 답변의 깊이를 조절하세요:
- 난이도 "상": 깊은 기술 이해와 실무 경험 기반 질문
- 난이도 "중": 개념적 이해를 묻는 질문
- 난이도 "하": 기본 개념을 묻는 질문

---
[TIL 본문] {til_content}

[관련 유사 질문 리스트]
- {similar_question_1}
- {similar_question_2}
- {similar_question_3}

[선택한 난이도] {difficulty}

---
출력 형식:     Question: {면접 질문 한 개}
             Answer: {해당 질문에 대한 모범 답변}
"""
```

- **retrieved_questions**: Qdrant에서 검색해온 유사 질문 리스트
- **user_til**: 사용자가 입력한 학습 내용

<h2>📌 RAG 적용 전/후 비교 및 검증 계획</h2>

항목 | RAG 미적용 | RAG 적용 후
-- | -- | --
질문 정확도 | 문법/문맥 일치 | 유사성 질문 기반 강화
답변 일관성 | 일관성 부족 | 관련 질문 맥락 반영
재사용성 | 매 요청마다 새로 생성 | 검색 결과 기반으로 효율 증가
검증 계획 |   | BLEU, ROUGE, BERTScore

<h2>📌 RAG 미도입 경우</h2>
<p><strong>단순 조합 구조:</strong></p>
<pre><code>사용자 TIL → Prompt 구성 → 질문 &amp; 답변 생성 → 응답 반환
</code></pre>
<p><strong>문제점</strong></p>
<ul>
<li>생성 모델만 사용할 경우 질문 품질이 랜덤에 가까워짐</li>
<li>난이도 조정, 주제 일치성 확보가 어려움</li>
<li>반복 생성 시 품질 편차 발생</li>
</ul>
<p><strong>대안</strong></p>
<ul>
<li>주기적 문서 수집 및 fine-tuning 기반 추가 학습</li>
<li>데이터셋 증강(Augmentation) 및 pre-prompting 강화</li>
</ul>

<h2>📌 서비스 목표와의 RAG 반영의 부합성</h2>

요구사항 | RAG 반영 이유
-- | --
맞춤형 질문 생성 | TIL 기반으로 의미 유사 질문 선별 및 생성
다양한 도메인 대응 | 태그 기반 검색 및 프롬프트 조정 가능 (Tech, AI, CS 등)
답변 품질 개선 | 문맥에 맞는 질문 유도 → 더 깊은 답변 생성 가능
확장성 | 새로운 주제 추가 시 데이터만 업로드하면 바로 대응 가능


