### 모델 다운로드(HuggingFace Hub)

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="google/gemma-3-1b-it",
    # token="hf_your_actual_token",  # 여기 본인의 토큰 입력
    local_dir="/home/mmm060400/KTB/models/gemma-3-1b-it",      # 저장될 디렉토리 이름(GCP 폴더)
    resume_download=True           # 중단된 다운로드 이어받기 가능
)
```

### vLLM 모델 로드

```bash
from vllm import LLM, SamplingParams
import torch

# 모델 위치
gemma_3_1b_it =  "/home/mmm060400/KTB/models/gemma-3-1b-it/"
# 모델 구동
# 1. 모델 디렉토리 경로
# 2. GPU 메모리 최대 사용치
# 3. GPU 병렬 개수
# llm = LLM(model=model_path, gpu_memory_utilization=0.95, tensor_parallel_size=1, max_model_len = 2048)
llm = LLM(model=gemma_3_1b_it, 
          gpu_memory_utilization=0.95, 
          dtype= torch.bfloat16,
          tensor_parallel_size=1, 
          max_model_len = 2048,)
```

### vLLM Inference(모든 모델 동일한 프롬프트 형식)

```python
from datetime import datetime
now = datetime.now().strftime('%Y-%m-%d')
lang = dataset["train"][0]["lang"] # github code review 데이터

prompt = f"""
You are an assistant that writes formal, markdown-based technical "Today I Learned (TIL)" reports in Korean, based on Git code diffs. Each TIL should be clear, neutral, and suitable for documentation or internal team sharing.

The programming language used in the code diff is **{lang}**.
Please consider syntax conventions and usage patterns specific to this language when explaining the changes.

Your writing should follow this structure:
- Begin with a markdown title line containing the current date: `# {now} TIL`
- Summarize the key changes in a **bullet-point list**, using a formal tone
- When referencing a code change, **include a code snippet right after the relevant bullet point**
- All bullet points must end consistently with periods
- If applicable, identify and explain potential issues related to **accessibility, scalability, or maintainability**
- For components using props like `$isExpanded`, `$isDisabled`, etc., briefly describe their function and recommend a good state management approach (e.g., Zustand, Redux)
- Avoid emotional or personal expressions like "I think", "I learned", or "I found"

Assume that any line starting with `@@ -0,0 +` indicates new code, and should be analyzed carefully.

Please write the answer **in Korean**, but the question is in English.

---

**Question (in English):**

"Please write a TIL based on the following code diff. Focus on the important changes and explain what might have been learned."

Code Diff:
{code}

---

**Answer (in Korean, Markdown format):**
"""
```

## vLLM 추론 속도 비교

동일한 질문에 대한 응답 속도 비교

| 모델 | speed input | speed output | VRAM 용량 | 답변 품질 | 상용화 가능 여부 |
| --- | --- | --- | --- | --- | --- |
| Gemma3-4b-it | 0.86 toks/s | 28.21 toks/s | 21000MiB / 23034MiB | 대체적으로 만족스러움 | 가능 |
| Gemma3-1b-it | 1.19 toks/s | 86.35 toks/s | 21902MiB / 23034MiB | 매우 낮음, 거짓말 다수, 답변 형식 부족 | 가능 |
| llama3.1-8b-it | 0.17 toks/s | 16.07 toks/s | 22084MiB / 23034MiB | 만족스러운 답변 수준 | 불가능 |
| deepseek-r1-qwen-7b | 1.07 toks/s | 16.78 toks/s | 22038MiB / 23034MiB | 답변 길이가 짧고 성의 없음 | 가능 |
| Qwen2.5-7b-it-1m | 0.30 toks/s | 16.85 toks/s | 22036MiB / 23034MiB | 성의 부족, 형식화되지 않음 | 가능 |

---

## llama-cpp-python 추론 속도 비교

| 모델 | speed input | speed output | VRAM 용량 | 답변 품질 |
| --- | --- | --- | --- | --- |
| Qwen2.5-coder-3b.gguf (6bit) | 14.72 ms/token | 67.95 tokens/s | 5938MiB / 23034MiB | 코드 해석 우수, TIL 작성은 형식 부족 |
| Gemma3-4b-it.gguf (6bit) | 14.76 ms/token | 67.76 tokens/s | 5970MiB / 23034MiB | 양자화 후 한국어 품질 저하 발생 |

---

## llama-cpp-python VS vLLM

| 항목 | vLLM | llama-cpp-python |
| --- | --- | --- |
| 제공 모델 | Hugging Face 기반 FP16 모델 | GGUF 형식의 경량화 모델 |
| 실행 환경 | CUDA 필수 (GPU) | CPU 또는 GPU |
| 지원 기능 | 비동기, KV 캐시, Tensor Parallel 지원 | 로우 레벨 추론, 다양한 양자화 지원 |
| 특징 | 대규모 LLM 서버 추론 최적화 | 초경량 추론 최적화 |
| 장점 | - GPU 활용 최적화 (`PagedAttention`)<br>- 다중 요청 처리에 강함<br>- `vllm.serve()`로 OpenAI 호환 API 제공<br>- FastAPI 연동 쉬움 | - 매우 낮은 메모리 점유 (INT4, INT8)<br>- CPU 기반 가능<br>- 가벼운 모델(1~4B) 추론 속도 빠름<br>- embedding / streaming 지원 |
| 단점 | - VRAM 많이 사용<br>- 모델 로딩 무겁고 느림<br>- 작은 GPU에 부적합 | - 출력 품질 낮을 수 있음<br>- GPU 병렬/서버 최적화 부족<br>- 대규모 트래픽 대응 어려움 |
| FastAPI 연동 | `vllm.serve()` 후 FastAPI proxy 구성 | `llama_cpp.server` 내장 or FastAPI 직접 구성 |

---

<h3>LLM 한국어 성능 측정</h3>
<p>SK Telecom에서 만든 벤치마크 데이터셋 기준 LLM 한국어 능력 평가 진행(f1-score 기준)

<code>lm-evaluation-harness</code> : 다양한 벤치마크에서 언어 모델의 성능을 자동으로 평가할 수 있는 프레임워크</p>
<ul>
<li><strong>KB-BoolQ</strong>: 문단에서 주어진 질문에 대해 참 또는 거짓을 판단</li>
<li><strong>KB-COPA</strong>: 주어진 상황에 가장 적합한 결과를 두 가지 대안 중에서 선택</li>
<li><strong>KB-WiC</strong>: 같은 단어가 서로 다른 문맥에서 같은 의미로 사용되는지 판단</li>
<li><strong>KB-HellaSwag</strong>: 상황 설명에 맞는 다음 전개를 네 가지 선택지 중에서 고름</li>
<li><strong>KB-SentiNeg</strong>: 문장의 긍정 또는 부정을 정확히 분류하는 능력을 평가</li>
</ul>

모델 | kobest_boolq | kobest_copa | kobest_hellaswag | kobest_sentineg | kobest_wic
-- | -- | -- | -- | -- | --
Mistral-7B-Instruct-v0.2 | 0.8145 | 0.5832 | 0.4860 | 0.5239 | 0.3438
Llama-3.1-8B-Instruct | 0.5869 | 0.6224 | 0.4238 | 0.8246 | 0.3280
Qwen2.5-7B-Instruct-1M | 0.5279 | 0.6963 | 0.5540 | 0.7237 | 0.3280
kanana-nano-2.1b-instruct | 0.6561 | 0.7896 | 0.4854 | 0.9748 | 0.3280
EXAONE-Deep-7.8B | 0.6728 | 0.6315 | 0.3786 | 0.3511 | 0.4023
Gemma-2-9B-Instruct-4Bit-GPTQ | 0.8105 | 0.7397 | 0.4423 | 0.7589 | 0.3297
Gemma-2-9b-it | 0.9152 | 0.7485 | 0.4520 | 0.8699 | 0.3276
Gemma-3-12b-it | 0.9160 | 0.8197 | 0.4658 | 0.9267 | 0.3976
