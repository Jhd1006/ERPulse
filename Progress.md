markdown# ERPulse 진행 사항

**마지막 업데이트:** 2026-07-02  
**상태:** Terraform 인프라 구축 완료 → FastAPI 앱 개발 시작

---

## ✅ 완료된 항목

### Phase 1: AWS 계정 및 IAM 설정
- **AWS 계정 생성** ✓
- **IAM 사용자 `erpulse-admin` 생성** ✓
  - `AdministratorAccess` 정책만 할당
  - Access Key 및 Secret Key 발급 완료

### Phase 2: Terraform 인프라 프로비저닝
- **VPC** (10.0.0.0/16), Public 서브넷 2개, Private 서브넷 2개 ✓
- **IGW, NAT Gateway, 라우트 테이블** ✓
- **EKS 클러스터** `erpulse-cluster` (v1.36) ✓
- **노드 그룹** `erpulse-node-group` (t3.medium × 2, Active) ✓
- **RDS PostgreSQL** `erpulse-db` (db.t3.micro, single-AZ) ✓
- **ECR** `erpulse-api` ✓
- **보안 그룹** (EKS, RDS) ✓
- **IAM Role** (클러스터/노드) ✓
- `kubectl get nodes` 정상 확인 ✓

---

## 🔄 진행 중 / 다음 단계

### Phase 3: FastAPI 앱 개발

#### 목표 디렉토리 구조
erpulse-api/
├── app/
│   ├── main.py          # FastAPI 진입점
│   ├── config.py        # 환경변수 설정
│   ├── database.py      # PostgreSQL 연결
│   ├── redis_client.py  # Redis 연결
│   ├── models.py        # DB 모델
│   ├── schemas.py       # Pydantic 스키마
│   ├── routers/
│   │   └── hospitals.py # 응급실 API 라우터
│   └── services/
│       ├── collector.py # 공공 API 수집 로직
│       └── fallback.py  # Fallback 로직
├── Dockerfile
├── requirements.txt
└── .env.example

#### 작업 순서
- [ ] FastAPI 기본 뼈대 (라우터, 헬스체크, 설정 구조)
- [ ] PostgreSQL 연결 (모델 + 마이그레이션)
- [ ] 공공 응급의료 API 연동 (데이터 수집)
- [ ] Redis Fallback 로직
- [ ] Dockerfile
- [ ] docker-compose로 로컬 테스트 (PostgreSQL + Redis)

---

## 📋 이후 단계 (Phase 3 완료 후)

1. **Docker 이미지 빌드 + ECR 푸시**
2. **GitHub Actions CI 구성** (테스트 → 빌드 → ECR 푸시 → manifest repo 업데이트)
3. **ArgoCD CD 구성** (GitOps)
4. **모니터링** (Prometheus + Grafana + Alertmanager + Slack)
5. **고가용성 검증 시나리오 실행**

---

## 📌 핵심 설계 결정

| 항목 | 선택 | 이유 |
|---|---|---|
| **DB** | RDS PostgreSQL | DB 운영 부담 제거, HA 검증에 집중 |
| **캐시** | Redis | TTL 15~30분으로 Fallback 전략 구현 |
| **IaC** | Terraform | 반복적 삭제/재생성 환경 일관성 보장 |
| **CD** | ArgoCD | GitOps, app repo와 manifest repo 분리 |
| **배포** | Argo Rollouts | Canary로 무중단 배포 검증 |
| **HPA 임계값** | CPU 70% | k6 부하 테스트로 75%부터 응답시간 증가 확인 |
| **RDS Multi-AZ** | false | 포트폴리오 환경, 비용 절감 |

---

## ⚠️ 핵심 교훈

- `deletion_protection = false` 누락 시 RDS 삭제 실패
- `aws_security_group`에는 `force_destroy` 인수 없음
- `apply` 후 코드 변경 시, `destroy` 전에 반드시 `apply` 한 번 더 실행
- Terraform 작업은 Claude Code 사용 선호 (파일 컨텍스트 일관성)

---

## 🔗 레포

- `erpulse-api` - FastAPI 소스코드 **(현재 작업 중)**
- `erpulse-manifest` - Kubernetes 배포 매니페스트 (ArgoCD 감시)
- `erpulse-infra` - Terraform 코드 (완료)

---

## 📌 핵심 설정값

| 항목 | 값 |
|---|---|
| VPC CIDR | 10.0.0.0/16 |
| EKS 버전 | 1.36 |
| 노드 타입 | t3.medium × 2 |
| RDS | PostgreSQL, db.t3.micro, single-AZ |
| ECR 저장소명 | erpulse-api |
| CronJob 주기 | 5분 |
| Redis TTL | 15~30분 |
| HPA CPU 임계값 | 70% |
| IAM 사용자 | erpulse-admin (AdministratorAccess) |