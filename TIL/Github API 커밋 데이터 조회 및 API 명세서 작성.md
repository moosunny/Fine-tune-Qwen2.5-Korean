# 날짜: 25.04.15

## Github API 커밋 데이터 조회

### 🚨 고려사항

- FastAPI를 활용한 정보 조회(GET) 기능 → Til 생성은 POST로 구현
- 커밋 기반 TIL을 생성하기 위해서는 코드 변경 이력 + 변경된 코드의 전체 내용
- sha: 고유 커밋 id를 활용하여 변경된 전체 코드 내용 조회 가능
- JSON 파일 형식으로 구성하여 최신 코드에 대한 당일 코드 변경 이력 저장

```python
import requests
from datetime import datetime
from collections import defaultdict
import re
import json

headers = {"Authorization": f"token {GITHUB_TOKEN}"}

username = "moosunny"
repo = "Translator_Practice" # Transformer 번역 모델 실습 레포지토리
date_str = "2025-03-05"

# 날짜 범위
since = f"{date_str}T00:00:00Z"
until = f"{date_str}T23:59:59Z"

# 커밋 목록
commits_url = f"https://api.github.com/repos/{username}/{repo}/commits"
params = {"since": since, "until": until, "per_page": 100}
commits = requests.get(commits_url, headers=headers, params=params).json()

file_data = defaultdict(lambda: {"filepath": "", "latest_code": "", "patches": []})

# 이미지/링크 포함 라인 제거 정규표현식
markdown_filter = re.compile(r"(!\[.*?\]\(.*?\)|http[s]?://)")

def remove_markdown_links(text: str) -> str:
    """이미지/링크 포함된 줄 제거"""
    lines = text.splitlines()
    filtered = [line for line in lines if not markdown_filter.search(line)]
    return "\n".join(filtered)

for commit in commits:
    sha = commit["sha"]
    commit_message = commit["commit"]["message"]

    commit_detail_url = f"https://api.github.com/repos/{username}/{repo}/commits/{sha}"
    commit_detail = requests.get(commit_detail_url, headers=headers).json()

    for file in commit_detail.get("files", []):
        filepath = file.get("filename", "")
        patch = file.get("patch", "")
        raw_url = file.get("raw_url", "")

        # 최신 코드 불러오기 및 필터
        if not file_data[filepath]["latest_code"] and raw_url:
            latest_code_res = requests.get(raw_url, headers=headers)
            if latest_code_res.status_code == 200:
                filtered_code = remove_markdown_links(latest_code_res.text)
                file_data[filepath]["latest_code"] = filtered_code

        # patch도 마찬가지로 필터링
        filtered_patch = remove_markdown_links(patch) if patch else ""

        # 데이터 저장
        file_data[filepath]["filepath"] = filepath
        file_data[filepath]["patches"].append({
            "commit_message": commit_message,
            "patch": filtered_patch
        })

# 최종 결과 구성
result = {
    "username": username,
    "repo": repo,
    "files": list
}

# defaultdict → 일반 dict로 변환
result["files"] = list(file_data.values())

# 출력
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### Til 생성 API 설계

- request methd: POST
- url: /user/til_generate
- Type:
    - e-mail: String
    - repo: String
    - files: List
        - filepath: String
        - latest_code: String
    - patches: List
        - commit_message: String
        - patch: String
  - 명세
    - emial: 유저 이메일
    - repo: 레포지토리
    - files: 변경 이력 데이터를 담은 리스트(당일에 커밋이 수행된 파일이 다수임을 고려)
    - filepath: 변경된 코드 파일
    - latest_code: 코드 파일 내용
    - patches: 코드 변경 내용과 커밋 메시지를 담은 리스트(한개의 파일별로 커밋 개수가 다수임을 고려)
    - commit_message: 커밋 메시지
    - patch: 코드 변경 내용

```json


{
  "email": "a01088415234@gmail.com",
  "repo": "Translator_Practice",
  "files": [
    {
      "filepath": "main.py",
      "latest_code": "import pandas as pd\nimport numpy as np\nimport torch\nimport torch.nn as nn\nimport torch.optim as optim\nfrom torch.optim....",
      "patches": [
        {
          "commit_message": "Add files via upload",
          "patch": "@@ -0,0 +1,135 @@\n+import pandas as pd\n+import numpy as np\n+import torch\n+import torch.nn as nn\n+import torch.optim as optim\n+from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts\n+\n+from Transformer import *\n+from transformers import MarianMTModel, MarianTokenizer # MT:..."
        }
      ]
    },
    {
      "filepath": "Train.py",
      "latest_code": "import torch\nimport math\...",
      "patches": [
        {
          "commit_message": "Train, Test Update, Complete",
          "patch": "@@ -1,112 +1,121 @@\n import torch\n import math\n-# from transformers import Token\n import matplotlib.pyplot as plt\n from tqdm import tqdm\n \n+class NoamScheduler:\n+    def __init__(self, optimizer, d_model, warmup_steps, LR_scale = 1):\n+ ..."
        }
      ]
    }
```

### Til 생성 후 데이터 전달을 위한 API 설계
- email: 유저 이메일
- repo: 레포지토리
- title: TIL 제목
- keyword: TIL 내용 반영한 키워드(1개 ~ 3개)
- content: TIL 본문
```json


{
  "email": "a01088415234@gmail.com",
  "repo": "repo1",
  "title": "2025-03-05 TIL - Kakao 로그인 요청 방식 개선",
  "keywords": ["빌더 패턴", "로그인 요청", "테스트 코드"],
  "content": "# 2025-03-05 TIL\n\n- KakaoLoginRequest 객체를 생성자 방식에서 빌더 패턴으로 변경하였습니다.\n  ```java\n  KakaoLoginRequest.builder()\n      .kakaoId(\"kakao123\")\n      .deviceToken(\"deviceToken\")\n      .build();\n  ```\n- 빌더 패턴은 가독성을 높이고, 선택적 인자 사용이 가능하며, 유지보수에 유리합니다.\n- 테스트 코드에서 초기화 방식이 명확해졌으며, 인자 순서 실수를 방지할 수 있습니다."
}

```

### 🗒️ 향후 예정 작업

1. FastAPI 연동하여 vLLM 과 연동하기
2. 코드 전체 데이터를 프롬프트에 넣기 VS 요약하여 Til 생성 모델 latency, throughput 측정하기
3. 파일 확장자 기반 필터링(`.py`, `.js`, `.java`, `.ts`, `.html`, `.css` 등 분석 대상 언어만 유지)
4. 파일 경로 기반 필터링(`tests/`, `docs/`, `.github/`, `node_modules/`, `venv/`, `__pycache__/`, `build/`, `dist/`, `assets/`, `images/`)
5. 패치(patch) 내 의미 없는 변경 필터링(단순 줄바꿈, 띄어쓰기 수정, 주석만 변경한 경우 무시)
