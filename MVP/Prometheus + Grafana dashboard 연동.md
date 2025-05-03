참고 링크: [Prometheus + Grafana 적용기](https://velog.io/@betalabs/Prometheus-Grafana-%EC%A0%81%EC%9A%A9%EA%B8%B0)

## Prometheus란?

metric 수집, 시각화, 알림 등을 제공하는 오픈소스 모니터링 시스템

## Prometheus 설치 전 GCP 방화벽 설정

- **VPC 네트워크 > 방화벽 규칙**으로 이동
- `방화벽 규칙 만들기`
- 아래와 같이 입력:
    - **이름**: `allow-prometheus-9090` (또는 원하는 이름)
    - **대상**: `모든 인스턴스`
    - **소스 IP 범위**: `0.0.0.0/0` (or 내 IP만: `XXX.XXX.XXX.XXX/32`)
    - **포트**: `9090` (또는 `3000,9090,9100` 같이 쉼표로 여러 개)

## 1. Prometheus 설치(9100번 포트)

```bash
sudo apt-get update
sudo apt-get install -y prometheus prometheus-node-exporter prometheus-pushgateway prometheus-alertmanager
```

Prometheus 버전 확인

- `prometheus —version`

---

## **2. Grafana 설치(3000번 포트)**

```bash
# 1. GPG 키 추가
sudo apt-get install -y gnupg2 curl
curl -fsSL https://apt.grafana.com/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/grafana.gpg

# 2. APT 저장소 추가
echo "deb [signed-by=/usr/share/keyrings/grafana.gpg] https://apt.grafana.com stable main" | \
  sudo tee /etc/apt/sources.list.d/grafana.list

# 3. 설치
sudo apt-get update
sudo apt-get install grafana

# 4. grafana 서버 시작
sudo systemctl start grafana-server
sudo systemctl status grafana-server

# 인스턴스 시작마다 그라파나 자동 실행
systemctl enable grafana-server
```

### Grafana 로그인(url: <GCP 외부 IP>/3000)

- 초기 로그인 정보
    - username: admin
    - password: admin(변경가능)

![Image](https://github.com/user-attachments/assets/a7b41cef-db9c-4917-b5b2-ed354daacd66)

---

## 3. node_exporter 설치

`node_exporter`는 서버의 리소스를 수집하여 `metric`을 제공

```bash
sudo apt-get update
sudo apt-get install prometheus-node-exporter
```

`node_exporter`를 `systemctl`명령어로 실행하기 위해 아래의 명령어를 통해 파일을 작성

```bash
sudo vi /etc/systemd/system/prometheus-node-exporter.service

---
# 이어서 아래 내용 복붙
 [Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus-node-exporter

[Install]
WantedBy=multi-user.target
```

`node_exporter`실행 및 재기동 시 자동으로 `node_exporter`가 실행이 되도록 설정

```bash
sudo systemctl daemon-reload
sudo systemctl start prometheus-node-exporter # node_exporter 실행
sudo systemctl enable prometheus-node-exporter # 재기동시 node_exporter 자동으로 실행되도록 설정
```
