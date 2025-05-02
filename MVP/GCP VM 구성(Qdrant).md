# 1. GCP VM 생성(qdrant-server)

### GCP VM 기본정보

![Image](https://github.com/user-attachments/assets/8f37e98d-e624-4ef8-8d6e-308f6fd772a8)

### GCP VM 구성

![Image](https://github.com/user-attachments/assets/48177717-32a9-4913-b603-e1bc02e30064)

### GCP VM 저장공간 및 OS

![Image](https://github.com/user-attachments/assets/d7ee9962-dd80-4811-b9ec-b30d9a6f8a33)

---

# 2. Ubuntu 도커 설치(22.04 LTS)

1. **Ubuntu 패키지 설치 업데이트**

```bash
sudo apt-get update
```

1. **필요한 패키지 설치**

```bash
sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

1.  **Docker의 공식 GPG키를 추가**

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

```

1. Docker 레포지토리 등록

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

```

1. **시스템 패키지 업데이트**

```bash
sudo apt-get update
```

1.  **Docker 설치**

```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

1. **Docker 설치 확인**

```bash
docker --version
```

### 🚨 Permission Error 뜰 경우

터미널에 순서대로 입력

```bash
# 1. 사용자 docker 그룹에 추가
sudo usermod -aG docker $USER

# 2. 그룹 변경 적용 (현재 터미널 세션에)
newgrp docker

# 3. 다시 확인
docker ps

# 4. 소켓으로 권한 확인
**ls -l /var/run/docker.sock**
```

---

# 3. Qdrant 설치 및 접근

1. Qdrant 이미지 설치

```bash
docker pull qdrant/qdrant
```

1. Qdrant 컨테이너 실행(계속 Permission denied 문제 발생 하면 sudo 앞에 붙이기)
- 외부 IP로도 접근할 수 있게 하려면 6334번 포트도 열어야 함
- `—restart=always`: 인스턴스 재시작시 자동으로 컨테이너 실행

```docker
docker run -d --name qdrant-test-server \
  -p 6333:6333 \
  -p 6334:6334 \
  --restart=always \
  -v /home/<로컬 파일 경로>:/qdrant/storage \
  qdrant/qdrant
```

1. 외부 접근 허용을 위한 GCP 방화벽 추가
    - GCP 콘솔 접속
    - 좌측 메뉴 → **VPC 네트워크** → **방화벽 규칙** 클릭
    - "**방화벽 규칙 만들기**" 버튼 클릭
    - 아래처럼 설정(나머지 설정은 무시)

| 항목 | 값 |
| --- | --- |
| 이름 | allow-qdrant-ports |
| 대상 | 모두 (all instances) 또는 특정 VM 네트워크 태그 |
| 트래픽 방향 | 수신 (Ingress) |
| IP 범위 | `0.0.0.0/0` (테스트용: 모든 IP 허용) |
| 허용할 포트 | `6333,6334` |

---

# 4. Qdrant Web UI 접속

```bash
# GCP 인스턴스 외부 IP 복붙하기
http://<GCP 인스턴스 외부 IP>:6334/dashboard
```

![Image](https://github.com/user-attachments/assets/80e2bd8c-b197-401a-ae81-a7f0540c13d7)


---

# 5. Collection 생성 및 Collection Config 설정

- Web UI Console 창에서 입력 후 RUN 버튼 누르기

```sql
PUT collections/til_logs
{
  "vectors": {
    "size": 1024,
    "distance": "Cosine"
  }
}
```

| 항목 | 설정값 | 설명 |
| --- | --- | --- |
| `size` | 1024 | `bge-m3` 임베딩 벡터 길이 |
| `distance` | `Cosine` | 의미 기반 검색 최적화 |
| `on_disk` | `true` | 대용량 데이터 저장 시 RAM 사용 줄임 |
| `shard_number` | `1` | 단일 노드 환경에서 가장 효율적 |
| `quantization_config` | `int8` | 검색 속도 + 메모리 절약 (성능 손실 매우 낮음) |
| `indexing_threshold` | `10000` | 이 수 이상 point가 쌓이면 자동으로 HNSW 인덱싱 시작 |
| `memmap_threshold` | `200000` | 일정 이상 point는 디스크 매핑 처리 |
| `flush_interval_sec` | `10` | 10초마다 디스크에 flush (안정성 강화) |

```sql
# 실행 결과 출력

{
  "result": true,
  "status": "ok",
  "time": 0.234224984
}
```
