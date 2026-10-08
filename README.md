# ERPulse

응급의료기관의 실시간 병상 현황을 제공하고, 공공데이터 기반 좌표 계산과 카카오모빌리티 API 연동으로 실제 차량 이동시간까지 고려해 가장 가까운 가용 응급실을 찾아주는 API 서비스이자, AWS EKS 위에 GitOps 배포 파이프라인과 오토스케일링을 처음부터 끝까지 직접 설계·구축한 인프라 프로젝트입니다.

## 화면
<img width="437" height="692" alt="image" src="https://github.com/user-attachments/assets/b643374c-ff92-47d8-b3b1-dbf4bac0d871" /> 



## 핵심 기능

| 기능 | Endpoint | 설명 |
|---|---|---|
| 응급실 목록/상세 조회 | `GET /hospitals` | 전국 응급실 목록 및 상세 정보 조회 |
| 실시간 병상 조회 | `GET /hospitals/realtime` | 실시간 가용 병상 조회, Redis 캐시 fallback 적용 |
| 데이터 수집 | `POST /hospitals/collect` | 공공데이터포털(data.go.kr) API 연동해 병원 데이터 수집·적재, CronJob이 5분 주기로 자동 호출 |
| 가까운 응급실 검색 | `GET /hospitals/nearest` | 좌표 기준 가용 병상이 있는 응급실 조회. 1차로 haversine 직선거리로 상위 후보를 추리고(결정론적, DB 내 계산), 2차로 그 후보에 한해 카카오모빌리티 길찾기 API로 실제 차량 소요시간을 조회해 재정렬. API 실패 시 직선거리 순으로 자동 폴백 |

## 데이터 모델

`hospitals` 테이블 하나로 관리합니다 (공공데이터 응급의료기관 정보 + 좌표를 함께 저장).

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | Integer (PK) | 내부 식별자 |
| `hpid` | String, unique | 공공데이터 응급의료기관 코드 |
| `dutyName` | String | 병원명 |
| `dutyAddr` | String, nullable | 주소 |
| `dutyTel1` | String, nullable | 대표 전화번호 |
| `hvec` | Integer, nullable | 응급실 가용 병상 수 (실시간 API에서 수집) |
| `hvoc` | Integer, nullable | 수술실 가용 수 (실시간 API에서 수집) |
| `lat` / `lng` | Float, nullable | 좌표 (목록 API의 wgs84Lat/wgs84Lon, 별도 지오코딩 불필요) |
| `updated_at` | DateTime | 마지막 동기화 시각 |

스키마 변경 이력은 `api/alembic/versions/`에서 확인할 수 있습니다.

## 아키텍처

| 구성요소 | 역할 | 배포 방식 |
|---|---|---|
| erpulse-api | FastAPI 백엔드 (조회/수집 로직) | EKS Deployment + HPA |
| RDS PostgreSQL | 병원 정보 영구 저장 | Terraform 프로비저닝 |
| Redis | 실시간 병상 정보 TTL 캐시 (15~30분) | EKS 파드 (비용 절감) |
| erpulse-collector | 공공 API → DB 동기화 배치 | CronJob (5분 주기) |
| erpulse-migrate | DB 스키마 마이그레이션 | ArgoCD PreSync Hook (배포 직전 자동 실행) |
| ArgoCD | GitOps 지속 배포 | Helm 설치, git 변경 자동 감지·sync |
| kube-prometheus-stack | 클러스터 + 앱 메트릭 수집(ServiceMonitor) 및 시각화 | Slack 알림|
| Cluster Autoscaler | 노드 레벨 오토스케일링 | IRSA 기반 |

## CI/CD 흐름
<img width="1069" height="551" alt="image" src="https://github.com/user-attachments/assets/6d014980-f68e-4e17-90f8-f5d3ec567e62" />

1. **GitHub · main** — `api/` 코드 push
2. **GitHub Actions** — pytest → docker build, OIDC로 AWS 인증
3. **ECR push** — tag = git SHA, lifecycle: 최근 10개 이미지만 유지
4. **manifest 자동 커밋** — `kustomization.yaml`의 `newTag`를 CI가 직접 갱신
5. **ArgoCD** — git polling(~3분 간격)으로 새 커밋 감지 후 automated sync + selfHeal

- **트리거**: `api/**` 변경 시에만 자동 빌드(path filter).  ECR을 처음 생성시 workflow_dispatch로 최초 이미지 빌드
- **이미지 태그**: `:latest` 대신 git 커밋 SHA로 고정 — 배포 버전 추적과 git revert 롤백이 가능
- **매니페스트 자동 갱신**: 빌드 후 CI가 `kustomization.yaml`의 `images.newTag`를 직접 커밋. kustomize의 `images` 트랜스포머가 이 값으로 모든 매니페스트의 태그를 덮어쓰므로, 이 한 줄이 실제 배포 버전의 단일 진실 소스
- **배포**: ArgoCD가 `manifest/` 경로를 git polling(~3분 간격)으로 감지해 자동 sync — 개발자는 코드만 push하면 테스트→빌드→배포까지 자동으로 이어짐


## 프로젝트 구조

```
ERPulse
├── api/          FastAPI 소스코드
├── web/          정적 검색 UI (GPS 기반 가까운 응급실 찾기, 빌드 없이 브라우저에서 바로 실행)
├── manifest/     Kubernetes 배포 매니페스트 (ArgoCD가 감시하는 GitOps 대상)
├── infra/
│   ├── persistent/   상시 유지 리소스 (ECR, GitHub OIDC/IAM Role) — 최초 1회 apply
│   └── cluster/      재생성 리소스 (VPC/EKS/RDS/ArgoCD/모니터링) — apply/destroy 반복 
└── load-test/    k6 부하테스트 스크립트
```

## 기술 스택

| 역할 | 기술 |
|---|---|
| Backend | FastAPI, SQLAlchemy(asyncio), Alembic |
| Database | RDS PostgreSQL |
| Cache | Redis |
| IaC | Terraform (상시 리소스와 클러스터 state 분리, 클러스터 재생성은 apply 한 번) |
| Orchestration | EKS, Deployment/Service/HPA/CronJob |
| CI | GitHub Actions (OIDC 인증, paths-filter로 불필요한 빌드 스킵) |
| CD | ArgoCD (GitOps, kustomize 이미지 태그 자동 갱신) |
| Scaling | HPA(CPU 70%) + Cluster Autoscaler 이중 오토스케일링 |
| Monitoring | Prometheus, Grafana, Alertmanager, Slack, prometheus-fastapi-instrumentator |
| Testing | pytest, k6 |
| 외부 API | 공공데이터포털(data.go.kr) 응급의료정보, 카카오모빌리티 길찾기(Directions) |

## 빠른 시작

전체 AWS 인프라를 처음부터 구성하고 배포까지 재현하려면 **[SETUP.md](./SETUP.md)** 를 따라가세요.
`terraform apply`만으로는 끝나지 않고, GitHub Secret 등록·최초 이미지 빌드 등 몇 단계가 더 필요합니다.

로컬에서 API 코드만 띄워서 개발하려면 `api/` 디렉터리의 `docker-compose.yml`, `.env.example`을 참고하세요.

검색 UI(`web/index.html`)는 빌드 과정 없이 브라우저로 파일을 직접 열면 바로 동작합니다. 단, 내부 `API_BASE`가 배포된 LoadBalancer 주소를 가리켜야 하므로 SETUP.md 8단계를 참고하세요.

## 모니터링

- kube-prometheus-stack으로 클러스터 메트릭과 함께, FastAPI 앱 메트릭을 ServiceMonitor로 수집합니다.
- Google SRE 골든 시그널(RED + Saturation) 기준으로 대시보드를 구성했습니다. (Rate / Errors / Duration)

| 패널 | 지표 | 분류 |
|---|---|---|
| 초당 요청 수 / 엔드포인트별 요청 수 | `http_requests_total` | Rate |
| 5xx 에러율 | `http_requests_total{status="5xx"}` | Errors |
| p95 응답시간 | `http_request_duration_seconds` | Duration |
| CPU 사용률(requests 대비) · HPA 레플리카(현재/목표/최대) | cAdvisor, kube-state-metrics | Saturation |

- RED + Saturation 기준으로 대시보드 구성, HPA 목표(CPU 70%)를 기준선으로 표시해 "부하 → CPU → 스케일아웃 → 응답시간 회복" 흐름을 한 화면에서 확인
- `/metrics`, `/health`는 수집에서 제외 (스크랩·헬스체크 요청이 요청 수와 p95를 왜곡)
- 기본 히스토그램 버킷(0.1/0.5/1s)으로는 p95가 약 95ms 근처로 고정되는 문제가 있어 0.01~2.5s 8단계로 세분화
- EKS 관리형 컨트롤 플레인(scheduler, controller-manager, etcd)은 기본 스크랩 대상에서 제외해 상시 오탐 알림 제거
- Alertmanager → Slack: Pod CrashLoop, Ready 실패, HPA 최대 도달, collector Job 실패 등
<img width="2530" height="1249" alt="image" src="https://github.com/user-attachments/assets/45395bac-f244-4847-bf18-76c81d0c8b2a" />
<img width="1268" height="593" alt="image" src="https://github.com/user-attachments/assets/43845e71-2cfa-426a-8349-d123c3e08691" />

<img width="644" height="252" alt="image" src="https://github.com/user-attachments/assets/1b05911f-3b49-42fe-a42a-d999297fae18" />

  ## 고가용성 검증

- **부하테스트 (k6)**: 100 VU 최초 테스트에서 100% 실패 발견 → RDS 보안그룹 미스매치(EKS 노드 실제 SG 미허용) + Alembic 마이그레이션 미적용(테이블 부재) 두 가지 근본원인 규명·해결. 이후 26,368건 요청 **실패율 0%** 달성
- **HPA + Cluster Autoscaler 연동 검증** (k6 VU 50 / 약 11분, maxReplicas 15)
  - **1차 (2026-07)**: HPA가 2→4→8→13 replica로 스케일아웃, 노드 자동 증설까지 확인. 95,428 요청 처리, 실패율 0%, p95 570ms
  - **2차 (2026-10, 앱 메트릭 계측 후 재측정)**: 약 2분 30초 만에 Pod 2→15, 노드 2→3 자동 증설. 57,480 요청 중 실패 1건(TCP 연결 리셋, 0.00%), 5xx 0건. 서버 측 p95가 스케일아웃 중 약 0.93초 → 안정 후 약 0.47초로 회복(Grafana 확인), 클라이언트 측 p95 978ms
  - **요청 수가 줄어든 이유**: 1차 이후 공공 API 수집 누락 버그(`numOfRows` 200 제한)를 수정해 저장 병원 수가 최대 200곳 → 530곳으로 늘고 좌표 컬럼이 추가되어, `/hospitals/` 응답이 요청당 약 172KB로 커짐. 동일 VU에서 요청당 처리·전송 시간이 늘어 처리량이 감소한 것으로, 두 결과는 응답 크기가 다른 조건의 측정값
  - **발견한 한계**: Pod별 CPU를 보니 k6의 keep-alive 연결이 스케일아웃 이전 Pod에 고정되어 새 Pod로 트래픽이 고르게 분산되지 않음. CLB/kube-proxy가 연결 단위로 분산하기 때문 → ALB(IP 타깃) 기반 요청 단위 분산이 개선 과제
- **Pod 강제 삭제 복구**: ReplicaSet이 약 11초 만에 자동 복구
- **노드 장애 시뮬레이션 (cordon + drain)**: t3.medium의 노드당 최대 파드 수(ENI 기반) 한도로 재스케줄이 막히는 실제 HA 갭을 발견 → Cluster Autoscaler 도입 후 동일 시나리오에서 노드 자동 증설로 정상 재스케줄되는 것까지 검증
