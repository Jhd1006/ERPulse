markdown# ERPulse 진행 사항

**마지막 업데이트:** 2026-07-05  
**상태:** ArgoCD CD 구성 완료 (EKS → ArgoCD → Application 전 과정 `terraform apply` 한 번으로 재현) → 모니터링 구성 시작

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
- [x] FastAPI 기본 뼈대 (라우터, 헬스체크, 설정 구조)
- [x] PostgreSQL 연결 (모델 + 마이그레이션, Alembic)
- [x] 공공 응급의료 API 연동 (데이터 수집)
- [x] Redis Fallback 로직
- [x] Dockerfile
- [x] docker-compose로 로컬 테스트 (PostgreSQL + Redis)

### Phase 4: ArgoCD CD 구성
- [x] Terraform으로 ArgoCD 설치 (`helm_release`, `argoproj/argo-helm`)
- [x] `kubectl_manifest`(gavinbunney/kubectl)로 ArgoCD `Application` 자동 등록 (CRD 사전검증 문제 우회)
- [x] Kubernetes 매니페스트 작성 (deployment, service, configmap, hpa, cronjob) + `kustomization.yaml`로 묶음 관리
- [x] `secret.yaml`은 kustomize 밖에서 `kubectl apply`로 수동 관리 (실제 값이라 git에는 미포함)
- [x] EKS 내 Redis 파드 추가 (fallback 캐시, ElastiCache 대신 — 비용/재현성 이유)
- [x] metrics-server EKS addon 추가 (HPA CPU 메트릭 수집)
- [x] Service를 `LoadBalancer`로 전환 (외부 접근 경로 확보)
- [x] `terraform destroy` 시 LoadBalancer가 생성한 ELB로 인한 VPC 삭제 실패 방지 (`null_resource` destroy-time provisioner)

---

## 📋 이후 단계

1. **Docker 이미지 빌드 + ECR 푸시** ✓
2. **GitHub Actions CI 구성** (테스트 → 빌드 → ECR 푸시, OIDC 인증) ✓
3. **ArgoCD CD 구성** (GitOps, kustomize 기반 이미지 태그 관리) ✓
4. **모니터링** (Prometheus + Grafana + Alertmanager + Slack) ← 다음 단계
5. **고가용성 검증 시나리오 실행** (k6 부하테스트, 노드/파드 강제 종료 복구, Argo Rollouts Canary)

---

## 📌 핵심 설계 결정

| 항목 | 선택 | 이유 |
|---|---|---|
| **DB** | RDS PostgreSQL | DB 운영 부담 제거, HA 검증에 집중 |
| **캐시** | Redis (EKS 파드) | TTL 15~30분짜리 disposable 캐시라 영속성 불필요, ElastiCache 대비 추가 비용 없음 |
| **IaC** | Terraform | 반복적 삭제/재생성 환경 일관성 보장 |
| **CD** | ArgoCD | GitOps, 단일 repo 내 `manifest/` 경로 감시 (3-repo 분리는 개인 포트폴리오엔 오버헤드로 판단) |
| **CRD 리소스 생성** | `kubectl_manifest` (gavinbunney/kubectl) | 공식 `kubernetes_manifest`는 plan 시점 CRD 존재를 요구해 ArgoCD 설치 전 실패 → 스키마 사전검증 없는 provider로 대체 |
| **배포** | Argo Rollouts | Canary로 무중단 배포 검증 |
| **HPA 임계값** | CPU 70% | k6 부하 테스트로 75%부터 응답시간 증가 확인 |
| **RDS Multi-AZ** | false | 포트폴리오 환경, 비용 절감 |

---

## ⚠️ 핵심 교훈

- `deletion_protection = false` 누락 시 RDS 삭제 실패
- `aws_security_group`에는 `force_destroy` 인수 없음
- `apply` 후 코드 변경 시, `destroy` 전에 반드시 `apply` 한 번 더 실행
- `.gitignore`의 `MANIFEST`(Python 패키징용) 규칙이 Windows 대소문자 미구분 때문에 `manifest/` 폴더 전체를 가려버림 — 프로젝트에 안 맞는 보일러플레이트 규칙은 정리할 것
- Terraform 공식 `kubernetes_manifest`는 plan 시점에 CRD 스키마를 검증해서, ArgoCD 설치 전엔 `Application` 리소스를 만들 수 없음 (치킨-달걀 문제) → `kubectl_manifest`로 우회
- kustomize `resources`에 `.gitignore`된 파일(`secret.yaml`)을 넣으면 ArgoCD(git 기준 build)가 파일을 못 찾아 전체 동기화 실패 → secret은 kustomize 목록에서 빼고 `kubectl apply`로 별도 수동 관리
- Redis/metrics-server처럼 "당연히 있어야 할" 인프라도 Terraform에 명시적으로 없으면 존재하지 않음 — 완료 체크리스트에 있다고 실제로 떠 있는지는 별개 문제
- Service `type: LoadBalancer`가 만든 ELB는 Kubernetes cloud provider가 Terraform 모르게 생성 → `destroy` 시 VPC가 ELB에 막혀 실패할 수 있어 destroy-time provisioner로 사전 정리 필요
- Terraform/매니페스트 코드는 Claude Code가 직접 파일을 수정하지 않고 텍스트로 전달 → 직접 타이핑하며 문서화 작업 병행

---

## 🔗 레포

- `ERPulse` (단일 repo, github.com/Jhd1006/ERPulse) - FastAPI 소스코드(`api/`), K8s 매니페스트(`manifest/`), Terraform(`infra/`) 통합 관리
  - 원래 3-repo 분리(api/manifest/infra) 계획이었으나 개인 포트폴리오 규모엔 오버헤드라 단일 repo로 통합
  - CI 경로 필터(`dorny/paths-filter`)로 `manifest/`, `infra/` 변경 시 빌드 job 자동 스킵 (CI 무한루프 없음)

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
| ArgoCD 차트 버전 | argo-cd 7.7.11 (argoproj/argo-helm) |
| 외부 접근 | Service `type: LoadBalancer` (Classic ELB, in-tree cloud provider 자동 생성) |