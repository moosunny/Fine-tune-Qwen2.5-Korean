### 🗓️ 날짜: 25.04.10

### 목표: GCP VM 생성 및 CUDA toolkit, NVIDIA 드라이버 설치 + llama-cpp-Python 구동

## 1. GCP VM 구성

- CPU: Intel Cascade Lake(vCPU 8개, 메모리 32GB)
- GPU: NVIDIA L4 1ea
- 부팅 디스크 용량: 200GB(Ubuntu 20.04 x86/64)

## 2. NVIDIA 드라이버 설치

- Ubuntu 20.04 기반 인스턴스로 재설치 (기존 Debian은 backports 문제 등으로 VM 삭제 후 재생성)
- `nvidia-smi` 명령이 작동하지 않아 NVIDIA 드라이버 설치 진행
- GCP 문서를 참고하여 **권장 드라이버 버전 (550.144.03)** 수동 설치
- 이후 `nvidia-smi` 작동 확인 → L4 GPU, CUDA 12.4 정상 출력

```bash
sudo apt install nvidia-driver-550
nvidia-smi
```

## 3. CUDA Toolkit 12.4 설치

- `nvidia-smi`  실행 후 CUDA 버전 확인

![Image](https://github.com/user-attachments/assets/235141ba-4e16-4046-9c17-242ca503d1ed)

- NVIDIA 공식 레포지토리 추가 후 CUDA 12.4 설치 진행

```bash
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt update
sudo apt install cuda-toolkit-12-4

=> nvcc --version  # CUDA 12.4.131
```

## 4. `llama-cpp-python`  GPU 버전 설치

### ❌ 문제 발생

- `CMAKE_ARGS="-DLLAMA_CUBLAS=ON"` 플래그는 **deprecated**
- 이후 `GGML_CUDA=ON` 으로 수정했지만 여전히 CMake 빌드 실패
- 원인: **Anaconda의 내부 링커(`ld`)가 glibc 시스템 라이브러리를 인식 못함**
    - 이를 해결하기 위해 venv로 가상환경 재구성 진행

```bash
# llama-cpp-python Prebulit CUDA wheel 설치(성공)
pip install llama-cpp-python==0.2.77 \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124 \
  --no-cache-dir
```

### Qwen2.5-coder-3b-q6, Gemma-3-4b-it-6q gguf 모델 다운(구글 드라이브)

```bash
# gdown으로 구글 드라이브에서 gguf 파일 다운로드
# 형식: https://drive.google.com/file/d/15uSQ5m_l0Ty3w1XBastRweh3ZKqmUbZ4/view?usp=drive_link
# Qwen2.5-coder-3b-Q6
!gdown gdown https://drive.google.com/uc?id=15uSQ5m_l0Ty3w1XBastRweh3ZKqmUbZ4 -O /home/mmm060400/KTB/models/qwen2.5-coder-3b-instruct-q6_k.gguf
# Gemma-3-4b-it-Q6
!gdown https://drive.google.com/uc?id=15uSQ5m_l0Ty3w1XBastRweh3ZKqmUbZ4 -O /home/mmm060400/KTB/models/gemma-3-4b-it-Q6_K.gguf
```

### Qwen2.5-coder-3b 모델 로드 및 GPU 지원 확인

```python
from llama_cpp import Llama

code_llm = Llama(model_path="/home/mmm060400/KTB/models/qwen2.5-coder-3b-instruct-q6_k.gguf",
                n_ctx = 2048,
                 n_gpu_layers=100, # Qwen2.5-coder-3b 모델은 37개 layer 구성
                 verbose = True
                 )
```

<img width="412" alt="Image" src="https://github.com/user-attachments/assets/76bc376d-4844-4376-a13a-333d8c654504" />

| 36개 반복 레이어를 GPU로 이동 | 트랜트포머 block 전체를 CUDA에서 계산 |
| --- | --- |
| 총 37개 레이어 GPU 할당 성공 | 전체 모델이 GPU에서 동작 중 |
| CUDA 메모리 사용량: 약 2.4GB | Q6_K 6bit 모델이라 10%의 GPU 메모리 만을 사용 |

## 4. 모델 추론을 통한 GPU 성능 측정

- 실제 이전 CPU만을 활용한 추론에 비해 2배 이상 빠른 속도로 추론을 진행하는 것을 확인함

```python
# github commit data 기반 코드 리뷰를 Qwen2.5-coder-3b 모델로 추론 진행
query = dataset["train"][0]["code"]

output = code_llm(f"""주어진 코드 변경 데이터에 대한 코드 리뷰를 부탁해,
                  @@ -0,0 +0,00 @@ 라는 문구가 있으면 해당 줄에 코드 변경 이력이 있다는 내용이라 해당 부분에 집중해서 어떤 코드가 변경이 이루어졌는지 확인해줘
                  
                  질문: {query},
                  답변: 
                  """ ,
                  max_tokens=1024, 
                  stream=True, 
                  stop = "<|endoftext|>")

for word in output:
  print(word["choices"][0]["text"], end = "", flush=True)
  
# GPU(L4) 기반 추론 성능 결과
llama_print_timings:        load time =     493.09 ms
llama_print_timings:      sample time =    2474.95 ms /  1024 runs   (    2.42 ms per token,   413.75 tokens per second)
llama_print_timings: prompt eval time =     601.22 ms /   769 tokens (    0.78 ms per token,  1279.06 tokens per second)
llama_print_timings:        eval time =   15054.69 ms /  1023 runs   (   14.72 ms per token,    67.95 tokens per second)
llama_print_timings:       total time =   20635.41 ms /  1792 tokens
```

## 💡 배운 점

- Anaconda 환경은 glibc 링크 문제로 CUDA 연동에 취약할 수 있으므로, venv 활용
- 최신 `llama-cpp-python`은 `GGML_CUDA=ON`으로 설정해야 GPU 백엔드 사용 가능
- GCP에서는 L4 GPU 권장 드라이버를 명시적으로 확인하고 적용하는 것이 중요
