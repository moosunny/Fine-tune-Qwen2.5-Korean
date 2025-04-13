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

### vLLM 추론 속도 비교

동일한 질문에 대한 응답 속도 비교

| 모델 | speed input | speed output | VRAM 용량 | 답변 품질 |
| --- | --- | --- | --- | --- |
| Gemma3-4b-it | 0.86 toks/s | 28.21 toks/s |  21000MiB /  23034MiB | 대체적으로 만족스러움 |
| Gemma3-1b-it | 1.19 toks/s | 86.35 toks/s |  21902MiB /  23034MiB | 매우 낮음, 거짓말 다수, 답변의 형식 부족 |
| llama3.1-8b-it | 0.17 toks/s | 16.07 toks/s | 22084MiB /  23034MiB | 만족스러운 답변 수준 |
| deepseek-r1-qwen-7b | 1.07 toks/s | 16.78 toks/s | 22038MiB /  23034MiB | 답변 자체의 길이가 짧고, 성의가 없다. |
| Qwen2.5-7b-it-1m | 0.30 toks/s | 16.85 toks/s |  22036MiB /  23034MiB | 답변의 성의가 없고, 형식화되지 않음 |
