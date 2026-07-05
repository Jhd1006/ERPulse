markdown# ERPulse 진행 사항

**마지막 업데이트:** 2026-07-06  
**상태:** 모니터링 + 고가용성 검증(부하테스트, 노드/파드 복구) 완료 → Argo Rollouts Canary는 향후 과제로 보류

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

### Phase 5: 모니터링 구성
- [x] `helm_release`로 `kube-prometheus-stack`(Prometheus + Grafana + Alertmanager + node-exporter + kube-state-metrics) 설치
- [x] Alertmanager → Slack Incoming Webhook 연동 (`slack_webhook_url`을 sensitive 변수로 관리)
- [x] Alertmanager 기본 `receivers` 교체 시 `null` receiver 누락으로 reconcile 실패하던 문제 수정
- [x] 실제 알림(`KubeSchedulerDown` 등) Slack 수신 확인 — EKS 관리형 컨트롤 플레인이라 발생하는 known false positive로 확인

### Phase 6: 고가용성 검증
- [x] **k6 부하테스트로 HPA CPU 70% 임계값 검증**
  - 최초 100 VU 테스트에서 100% 실패 발견 → 근본 원인 2가지 규명 및 수정
    1. RDS 보안그룹이 EKS 노드의 실제 보안그룹(EKS 자동 생성분)을 허용하지 않던 미스매치
    2. Alembic 마이그레이션이 RDS에 한 번도 적용되지 않아 테이블 자체가 없었음
  - 수정 후 100 VU, 26368 요청 실패율 0% 달성 (커넥션 풀 크기는 기본값 그대로도 충분했음 → 애초에 풀 크기 문제가 아니었음)
  - CPU request/limit(100m/500m → 200m/1000m), HPA maxReplicas(4→8) 튜닝하며 반복 검증
  - 상세 결과는 `부하테스트 보고서` 참고
- [x] **노드/파드 강제 종료 후 자동 복구 확인**
  - 파드 삭제 → ReplicaSet이 약 11초 만에 자동 복구 (정상)
  - 노드 `cordon+drain` → 남은 노드가 **"Too many pods"(t3.medium의 max-pods 한도)** 로 재스케줄 실패하는 실제 HA 갭 발견
- [ ] Argo Rollouts Canary 배포 — 시간 관계상 향후 과제로 보류 (신규 컨트롤러 설치 + Deployment→Rollout 전환 + 실전 검증까지 필요해 범위가 커서 별도 세션으로 분리)

---

## 📋 이후 단계

1. **Docker 이미지 빌드 + ECR 푸시** ✓
2. **GitHub Actions CI 구성** (테스트 → 빌드 → ECR 푸시, OIDC 인증) ✓
3. **ArgoCD CD 구성** (GitOps, kustomize 기반 이미지 태그 관리) ✓
4. **모니터링** (Prometheus + Grafana + Alertmanager + Slack) ✓
5. **고가용성 검증 시나리오 실행** (k6 부하테스트 ✓, 노드/파드 강제 종료 복구 ✓, Argo Rollouts Canary는 보류)

---

## 📌 핵심 설계 결정

| 항목 | 선택 | 이유 |
|---|---|---|
| **DB** | RDS PostgreSQL | DB 운영 부담 제거, HA 검증에 집중 |
| **캐시** | Redis (EKS 파드) | TTL 15~30분짜리 disposable 캐시라 영속성 불필요, ElastiCache 대비 추가 비용 없음 |
| **IaC** | Terraform | 반복적 삭제/재생성 환경 일관성 보장 |
| **CD** | ArgoCD | GitOps, 단일 repo 내 `manifest/` 경로 감시 (3-repo 분리는 개인 포트폴리오엔 오버헤드로 판단) |
| **CRD 리소스 생성** | `kubectl_manifest` (gavinbunney/kubectl) | 공식 `kubernetes_manifest`는 plan 시점 CRD 존재를 요구해 ArgoCD 설치 전 실패 → 스키마 사전검증 없는 provider로 대체 |
| **배포** | 일반 Deployment 롤링 업데이트 | Argo Rollouts Canary는 설계만 하고 시간 관계상 향후 과제로 보류 |
| **HPA 임계값** | CPU 70% | k6 부하테스트로 검증. request/limit을 100m/500m→200m/1000m, maxReplicas 4→8로 튜닝 필요성 확인 |
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
- Terraform 공식 `aws_eks_cluster`가 반환하는 보안그룹(`resourcesVpcConfig.securityGroupIds`)과, 실제 워커 노드 EC2에 붙는 보안그룹은 다를 수 있음(EKS가 노드용으로 별도 자동 생성) — RDS 등 다른 리소스의 접근 허용 규칙은 `aws_eks_cluster.main.vpc_config[0].cluster_security_group_id`를 참조해야 함
- 부하테스트에서 커넥션 타임아웃이 나온다고 바로 "커넥션 풀 부족"으로 단정하지 말 것 — 네트워크(보안그룹)와 스키마(마이그레이션 적용 여부)부터 계층별로 검증해야 함. 실제 원인은 풀 크기가 아니라 이 두 가지였음
- HPA의 CPU 사용률(%)은 항상 **request 대비**로 계산됨 (limit·노드 전체 CPU와 무관). request를 낮게 잡으면 작은 절대량 변화에도 퍼센트가 크게 출렁임
- CPU `limit`은 파드가 실제로 쓸 수 있는 절대 상한(스로틀링 기준), `request`는 그 상한 대비 퍼센트 계산의 분모 — 이 둘의 역할이 다르므로 목적에 맞게 따로 조정해야 함
- `t3.medium`은 CPU/메모리 여유가 있어도 **노드당 최대 파드 수(ENI/IP 기반, 약 17개)** 한도로 인해 스케줄이 막힐 수 있음 — 노드 장애 시뮬레이션(cordon+drain)으로 실제 확인

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
| erpulse-api CPU request/limit | 200m / 1000m (기존 100m/500m에서 상향) |
| HPA minReplicas/maxReplicas | 2 / 8 (기존 max 4에서 상향) |
| 모니터링 차트 버전 | kube-prometheus-stack 65.5.1 |