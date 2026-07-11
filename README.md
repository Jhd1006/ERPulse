# ERPulse

Kubernetes 기반 응급의료 정보 서비스의 무중단 배포 및 장애 복구 검증 프로젝트

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
| Backend | FastAPI (Python) |
| Database | RDS PostgreSQL |
| Cache | Redis |
| Orchestration | EKS |
| IaC | Terraform |
| CI/CD | GitHub Actions + ArgoCD |
| Monitoring | Prometheus + Grafana |
| Scaling | HPA + Cluster Autoscaler |

## 빠른 시작

전체 AWS 인프라를 처음부터 구성하고 배포까지 재현하려면 **[SETUP.md](./SETUP.md)** 를 따라가세요.
Terraform apply만으로는 끝나지 않고, GitHub Secret 등록·최초 이미지 빌드 등 몇 단계가 더 필요합니다

로컬에서 API 코드만 띄워서 개발하려면 `api/` 디렉터리의 `docker-compose.yml`, `.env.example`을 참고하세요.

## 고가용성 검증 시나리오

1. Pod 강제 삭제 → 복구 시간 측정
2. Liveness Probe 실패 → 자동 재시작
3. 트래픽 급증 → HPA 스케일아웃 + Cluster Autoscaler 노드 증설
