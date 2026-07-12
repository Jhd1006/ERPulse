# ERPulse

응급의료기관의 실시간 병상 현황을 제공하는 API 서비스이자, AWS EKS 위에 GitOps 배포 파이프라인과 및 오토스케일링을 처음부터 끝까지 직접 설계·구축한 인프라 프로젝트

## 핵심 기능

| 기능 | Endpoint | 설명 |
|---|---|---|
| 응급실 목록/상세 조회 | `GET /hospitals` | 전국 응급실 목록 및 상세 정보 조회 |
| 실시간 병상 조회 | `GET /hospitals/realtime` | 실시간 가용 병상 조회, Redis 캐시 fallback 적용 |
| 데이터 수집 | `POST /hospitals/collect` | 공공데이터포털(data.go.kr) API 연동해 병원 데이터 수집·적재, CronJob이 5분 주기로 자동 호출 |

## 아키텍처

| 구성요소 | 역할 | 배포 방식 |
|---|---|---|
| erpulse-api | FastAPI 백엔드 (조회/수집 로직) | EKS Deployment + HPA |
| RDS PostgreSQL | 병원 정보 영구 저장 | Terraform 프로비저닝 |
| Redis | 실시간 병상 정보 TTL 캐시 (15~30분) | EKS 파드 (비용 절감) |
| erpulse-collector | 공공 API → DB 동기화 배치 | CronJob (5분 주기) |
| erpulse-migrate | DB 스키마 마이그레이션 | ArgoCD PreSync Hook (배포 직전 자동 실행) |
| ArgoCD | GitOps 지속 배포 | Helm 설치, git 변경 자동 감지·sync |
| kube-prometheus-stack | 메트릭 수집·시각화·알림 | Slack Webhook 연동 |
| Cluster Autoscaler | 노드 레벨 오토스케일링 | IRSA 기반 |

## CI/CD 흐름
<img width="1069" height="551" alt="image" src="https://github.com/user-attachments/assets/6d014980-f68e-4e17-90f8-f5d3ec567e62" />

1. **GitHub · main** — `api/` 코드 push
2. **GitHub Actions** — pytest → docker build, OIDC로 AWS 인증
3. **ECR push** — tag = git SHA, lifecycle: 최근 10개 이미지만 유지
4. **manifest 자동 커밋** — `kustomization.yaml`의 `newTag`를 CI가 직접 갱신
5. **ArgoCD** — git polling(~3분 간격)으로 새 커밋 감지 후 automated sync + selfHeal

- **트리거**: `api/**` 변경 시에만 자동 빌드(path filter). 인프라만 바뀐 경우엔 `workflow_dispatch`로 수동 트리거
- **이미지 태그**: `:latest` 대신 git 커밋 SHA로 고정 — 배포 버전 추적과 git revert 롤백이 가능
- **매니페스트 자동 갱신**: 빌드 후 CI가 `kustomization.yaml`의 `images.newTag`를 직접 커밋. kustomize의 `images` 트랜스포머가 이 값으로 모든 매니페스트의 태그를 덮어쓰므로, 이 한 줄이 실제 배포 버전의 단일 진실 소스
- **배포**: ArgoCD가 `manifest/` 경로를 git polling(~3분 간격)으로 감지해 자동 sync — 개발자는 코드만 push하면 테스트→빌드→배포까지 자동으로 이어짐


## 프로젝트 구조

```
ERPulse
├── api/          FastAPI 소스코드
├── manifest/     Kubernetes 배포 매니페스트 (ArgoCD가 감시하는 GitOps 대상)
├── infra/        Terraform 인프라 코드 (VPC/EKS/RDS/ECR/ArgoCD/모니터링)
└── load-test/    k6 부하테스트 스크립트
```

## 기술 스택

| 역할 | 기술 |
|---|---|
| Backend | FastAPI, SQLAlchemy(asyncio), Alembic |
| Database | RDS PostgreSQL |
| Cache | Redis |
| IaC | Terraform (VPC/EKS/RDS/ECR/IAM 단일 apply) |
| Orchestration | EKS, Deployment/Service/HPA/CronJob |
| CI | GitHub Actions (OIDC 인증, paths-filter로 불필요한 빌드 스킵) |
| CD | ArgoCD (GitOps, kustomize 이미지 태그 자동 갱신) |
| Scaling | HPA(CPU 70%) + Cluster Autoscaler 이중 오토스케일링 |
| Monitoring | Prometheus, Grafana, Alertmanager, Slack |
| Testing | pytest, k6 |

## 빠른 시작

전체 AWS 인프라를 처음부터 구성하고 배포까지 재현하려면 **[SETUP.md](./SETUP.md)** 를 따라가세요.
`terraform apply`만으로는 끝나지 않고, GitHub Secret 등록·최초 이미지 빌드 등 몇 단계가 더 필요합니다.

로컬에서 API 코드만 띄워서 개발하려면 `api/` 디렉터리의 `docker-compose.yml`, `.env.example`을 참고하세요.

## 고가용성 검증

- **부하테스트 (k6)**: 100 VU 최초 테스트에서 100% 실패 발견 → RDS 보안그룹 미스매치(EKS 노드 실제 SG 미허용) + Alembic 마이그레이션 미적용(테이블 부재) 두 가지 근본원인 규명·해결. 이후 26,368건 요청 **실패율 0%** 달성
- **HPA + Cluster Autoscaler 연동 검증**: maxReplicas 15, k6 VU 50/10분 부하 → HPA가 2→4→8→13 replica로 스케일아웃, 노드 자동 증설까지 확인. 95,428 요청 처리, 실패율 0%, p95 570ms
- **Pod 강제 삭제 복구**: ReplicaSet이 약 11초 만에 자동 복구
- **노드 장애 시뮬레이션 (cordon + drain)**: t3.medium의 노드당 최대 파드 수(ENI 기반) 한도로 재스케줄이 막히는 실제 HA 갭을 발견 → Cluster Autoscaler 도입 후 동일 시나리오에서 노드 자동 증설로 정상 재스케줄되는 것까지 검증
