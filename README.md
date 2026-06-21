# README.md 내용 작성
@"
# ERPulse

Kubernetes 기반 응급의료 정보 서비스의 무중단 배포 및 장애 복구 검증

## 프로젝트 구조

- `api/` - FastAPI 소스코드
- `manifest/` - Kubernetes 배포 매니페스트 (ArgoCD 감시)
- `infra/` - Terraform 인프라 코드

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

## 빠른 시작

\`\`\`bash
cd infra
terraform init
terraform plan
terraform apply
\`\`\`

## 고가용성 검증 시나리오

1. Pod 강제 삭제 → 복구 시간 측정
2. Liveness Probe 실패 → 자동 재시작
3. 트래픽 급증 → HPA 스케일아웃
"@ | Out-File README.md -Encoding UTF8 -Force

git add README.md
git commit -m "Update root README"
git push origin main