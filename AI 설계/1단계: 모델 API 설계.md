[AI api 명세 Template 구글 스프레드시트](https://docs.google.com/spreadsheets/d/1rRXZYbQd_aPK2ijTWzdA6RsStcZJAy0ZxAd9_azm_j0/edit?gid=1878554884#gid=1878554884)

<h1>📍Github Commit 데이터 기반 Til 생성 API📍</h1>
<div style="margin-left: 20px;">
<h3>✔️ 엔드포인트: <code>POST/user/til</code></h3>

스키마 항목 | Type | 설명
-- | -- | --
email | String | github 주소
date | String | YYYY-MM-DD
repo | String | 선택한 레포지토리
files | List |
&nbsp;>&nbsp;filepath | String | 파일 이름
&nbsp;>&nbsp;latest_code | String | 코드 본문
patches | List | 
&nbsp;>&nbsp;commit_message | String | 커밋 메세지 
&nbsp;>&nbsp;patch | String | 변경 사항
<!-- notionvc: 7981837a-4f2a-4eda-8cdd-01c365ab9dca -->

<h3>✔️ JSON body</h3>
<pre><code class="language-json">
{
      "email": "a01088415234@gmail.com",
      "date": "2025-04-14"
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
}
</code></pre>

<h3>✔️ response 예시</h3>
<pre><code class="language-json">
{
  &quot;user&quot;: &quot;test1@gmail.com&quot;,
  &quot;repo&quot;: &quot;repo1&quot;,
  &quot;title&quot;: &quot;2025-04-14 TIL - Kakao 로그인 요청 방식 개선&quot;,
  &quot;keywords&quot;: [&quot;빌더 패턴&quot;, &quot;로그인 요청&quot;, &quot;테스트 코드&quot;],
  &quot;content&quot;: &quot;# 2025-04-14 TIL\\n\\n- KakaoLoginRequest 객체를 생성자 방식에서 빌더 패턴으로 변경하였습니다.\\n  ```java\\n  KakaoLoginRequest.builder()\\n      .kakaoId(\\&quot;kakao123\\&quot;)\\n      .deviceToken(\\&quot;deviceToken\\&quot;)\\n      .build();\\n  ```\\n- 빌더 패턴은 가독성을 높이고, 선택적 인자 사용이 가능하며, 유지보수에 유리합니다.\\n- 테스트 코드에서 초기화 방식이 명확해졌으며, 인자 순서 실수를 방지할 수 있습니다.&quot;
}
</code></pre>

<h3>✔️ 응답 코드</h3>

| Code | Message                  | Etc                   |
|------|--------------------------|------------------------|
| 201  | Success                  | 생성 성공             |
| 400  | Bad Request              | 잘못된 입력값         |
| 500  | Internal Server Error    | AI 서버 오류  |
</li>
</div>

<h1>📍당일 Til 기반 모의 면접 질문지 생성 API (2차 MVP 서비스 출시)📍</h1>
<div style="margin-left: 20px;">
  <h3>✔️ 엔드 포인트: <code>POST/user/interview</code></h3>

  스키마 항목 | TYPE | 설명
  -- | -- | --
  email | String | github 주소
  date | String | YYYY-MM-DD
  difficulty | Int | (1:상, 2:중, 3:하) 택 1
  title | String | til 제목
  keywords | List[String] | til 키워드
  til | String | til 본문

  <h3>✔️ JSON body</h3>
  <pre><code class="language-json">
  {
    "email": "test@gmail.com",
    "date": "2025-04-11",
    "difficulty": 2,
    "title": "2025-04-14 TIL - Kakao 로그인 요청 방식 개선",
    "keywords": ["빌더 패턴", "로그인 요청", "테스트 코드"],
    "til": "오늘은 FastAPI 기반 백엔드 프로젝트에서 게시글 수정 기능을 리팩토링하고, 전체 API의 응답 형식을 통일하는 작업을 진행했다.\n\n[1] 작업한 주요 내용:\n1. 게시글 수정 API에서 입력값이 있는 필드만 조건적으로 업데이트하도록 수정했다.\n    기존에는 `post.title = post_update.title`처럼 무조건 값을 덮어썼지만,\n    이번에는 `if post_update.title:` 조건문을 활용해 선택적으로 필드를 갱신하도록 했다.\n2. 응답 메시지를 `{ message, data }` 형식으로 통일했다.\n    예전에는 단순히 객체만 리턴하거나 \"성공\"이라는 문자열만 리턴했지만,\n    이제는 구조화된 응답을 통해 프론트엔드가 더 예측 가능한 방식으로 데이터를 처리할 수 있게 되었다.\n3. 예외 처리를 전역적으로 일관되게 만들기 위해 커스텀 예외 클래스를 도입했다.\n    예를 들어, `raise HTTPException(...)` 대신 `raise NotFoundException(...)`처럼 변경하고,\n    전역 예외 핸들러에서 예외 로그를 출력하고 사용자에게는 깔끔한 메시지를 전달하도록 구성했다.\n\n[2] 오늘 배운 점:\n- FastAPI에서 `Optional[str]` 필드를 사용할 때, 빈 문자열과 `None`을 구분해서 처리해야 하는 경우가 많다는 점을 새삼 느꼈다. Pydantic의 유효성 검사 로직을 정확히 이해하고 있어야 한다.\n- API 응답을 구조화하면 Swagger 문서에서도 명확한 예시와 스키마가 출력되기 때문에, 프론트엔드와의 커뮤니케이션 비용이 줄어든다.\n- 예외 처리를 클래스화하면 코드 가독성이 높아지고, 나중에 로깅이나 메시지 포맷을 일괄적으로 관리할 수 있어서 유지보수 측면에서도 이득이다.\n\n[3] 오늘의 회고:\n예전에는 기능이 돌아가기만 하면 된다고 생각했지만,\n오늘은 코드의 구조적 일관성과 협업 시 예측 가능성을 많이 고려하면서 작업했다는 점에서 개발자로서 한 단계 성장한 느낌을 받을 수 있었다.\n혼자 개발할 때는 불필요해 보일 수 있는 부분도,\n팀 프로젝트에서는 ‘명확함’이 가장 큰 효율이라는 걸 다시 한 번 체감했다.\n\n[4] 내일 할 일:\n- 공통 응답 형식을 정의하는 Pydantic 모델 만들기\n- Swagger 문서에 각 API의 응답 예시(example) 추가\n- 게시글 삭제 기능에도 동일한 응답 포맷과 예외 처리 적용하기"
  }
  </code></pre>
  <!-- notionvc: af6de84d-f81d-462f-87f6-a4c4fd74c652 -->

  <h3>✔️ response 예시</h3>
  <pre><code class="language-json">
  {
    "title": "유효성 검사 질문",
    "content": [
      {
        "question": "FastAPI에서 POST 요청을 처리할 때, Pydantic을 통한 유효성 검사의 흐름을 설명해주세요.",
        "answer": "FastAPI에서는 요청 바디의 유효성 검사를 위해 Pydantic의 BaseModel을 사용합니다. 사용자가 정의한 Pydantic 모델을 엔드포인트의 파라미터로 선언하면, FastAPI는 자동으로 해당 모델을 기반으로 JSON body를 파싱하고, 필드별 타입 검증 및 필수 여부를 검사합니다. 유효하지 않은 데이터가 들어오면 FastAPI는 자동으로 422 응답과 함께 상세한 에러 메시지를 반환합니다. 이를 통해 복잡한 유효성 검사 로직 없이도 안정적인 API 요청 처리가 가능합니다."
      },
      {
        "question": "Pydantic의 BaseModel은 어떤 역할을 하나요?",
        "answer": "Pydantic의 BaseModel은 데이터 모델을 정의하고 입력값의 타입을 검증하는 데 사용됩니다. FastAPI에서 BaseModel을 상속받은 클래스를 사용하면, 해당 모델이 요청 본문의 구조와 타입을 명시적으로 정의하게 됩니다. 이를 통해 사용자 입력을 타입에 맞게 자동 변환하거나, 잘못된 타입일 경우 즉시 에러를 발생시킵니다. 또한 `.dict()`나 `.json()` 같은 메서드를 통해 데이터 직렬화/역직렬화도 간편하게 처리할 수 있어 API 설계와 개발을 훨씬 효율적으로 만들어줍니다."
      },
      {
        "question": "FastAPI에서 필수 입력값과 선택 입력값은 어떻게 구분하나요?",
        "answer": "FastAPI에서는 Pydantic 모델 정의 시 `Optional` 타입 또는 기본값을 지정하여 선택 입력값을 구분합니다. 예를 들어, `title: Optional[str] = None`처럼 선언하면 해당 필드는 요청 본문에 없어도 오류가 발생하지 않으며, 자동으로 `None`으로 처리됩니다. 반면 기본값 없이 타입만 지정된 `title: str`은 필수 입력값으로 간주되어, 요청에 포함되지 않으면 422 Unprocessable Entity 오류가 발생합니다. 이를 통해 각 입력 필드의 필수 여부를 명확히 관리할 수 있습니다."
      }
    ]
  }

  </code></pre>

  <h3>✔️ 응답 코드</h3>

  Code | Message                  | Etc                   |
  ------|--------------------------|------------------------|
  201  | Success                  | 생성 성공             |
  400  | Bad Request              | 잘못된 입력값         |
  500  | Internal Server Error    | AI 서버 오류  |

  </ul>
  <!-- notionvc: 8651adc3-9ebd-4ce4-af4d-821cea447354 -->
</div>


<h1>📍Tech News 요약본 생성 (3차 MVP서비스 출시)📍</h1>
<div style="margin-left: 20px;">
<h3>✔️ 엔드포인트: <code>POST/user/news</code></h3>

스키마 항목 | Type | 설명
-- | -- | --
date | String | YYYY-MM-DD
news | List | 
&nbsp;>&nbsp;title | String | 뉴스 제목
&nbsp;>&nbsp;content | String | 뉴스 본문 

<h3>✔️ JSON body</h3>
<pre><code class="language-json">
{
  "date": "2025-04-14",
  "news": [
    {
      "title": "메타, 차세대 멀티모달 AI 모델 ‘라마 4’ 시리즈 공개",
      "content": "메타가 차세대 인공지능 모델 시리즈 '라마(Llama) 4'를 공개하며 멀티모달 AI 경쟁에 본격 진입했다."
    },
    {
      "title": "깃랩 데브섹옵스 플랫폼에 AWS AI 코딩툴 '큐 디벨로퍼' 통합된다",
      "content": "아마존웹서비스(AWS)가 깃랩(GitLab)과 협력해 AI 코딩 어시스턴트인 큐 디벨로퍼(Q Developer)를 깃랩 듀오(GitLab Duo)에 통합한다고 17일(현지시간) 밝혔다."
    }
  ]
}
</code></pre>

<h3>✔️ response 예시</h3>
<pre><code class="language-json">
{
    "date": "2025-04-14",
    "count": 2,
    "summary": [
      "메타, 차세대 멀티모달 AI 모델 ‘라마 4’ 시리즈 공개",
      "깃랩 데브섹옵스 플랫폼에 AWS AI 코딩툴 '큐 디벨로퍼' 통합된다"
    ]
}
</code></pre>

<h3>✔️ 응답 코드</h3>

| Code | Message                  | Etc                   |
|------|--------------------------|------------------------|
| 201  | Success                  | 생성 성공             |
| 400  | Bad Request              | 잘못된 입력값         |
| 500  | Internal Server Error    | AI 서버 오류  |
</ul>
</div>

<h1>✅ 서비스 아키텍처 API 흐름 ✅</h1>
<div style="margin-left: 20px;">
<pre><code class="plaintext">
GitHub Commit
    ↓
[ /user/til ]
    ↓ (생성된 TIL)
[ /user/interview ] ← 난이도 선택 및 질문 생성
    ↓
클라이언트로 전달
</br>
기술 뉴스 입력
    ↓
[ /user/news ] → 요약 결과 제공
</pre></code>
</div>
