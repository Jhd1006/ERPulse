# SETUP.md — ERPulse 처음부터 재현하기

이 문서는 이 레포를 fork/clone한 사람이 자기 AWS 계정에 ERPulse를 처음부터 배포하는 전체 과정을 다룹니다.
`terraform apply` 한 번으로 끝나지 않고, 아래 순서를 그대로 따라가야 정상적으로 배포됩니다 — 순서를 건너뛰면 이미지가 없어서 `ImagePullBackOff`가 나거나, GitHub Actions가 AWS에 인증하지 못하는 등 실제로 겪었던 문제를 그대로 반복하게 됩니다.

---

## 0. 사전 요구사항

- AWS 계정 (IAM 사용자에 `AdministratorAccess` 권한 — 최소 권한으로 좁히려면 EKS/VPC/RDS/ECR/IAM 관련 정책 필요)
- Terraform >= 1.0
- AWS CLI (자격증명 설정 완료: `aws configure`)
- kubectl
- 자신의 GitHub 계정으로 이 레포를 fork

## 1. fork 시 반드시 바꿔야 하는 하드코딩 값

원본 레포(`Jhd1006/ERPulse`)를 기준으로 아래 3곳에 계정/레포 경로가 고정돼 있습니다. fork한 레포에서는 이 값들을 자기 것으로 바꿔야 GitHub Actions와 ArgoCD가 정상 동작합니다.

| 파일 | 위치 | 바꿀 값 |
|---|---|---|
| `infra/github_oidc.tf` | `values = ["repo:Jhd1006/ERPulse:ref:refs/heads/main"]` | 본인 `github계정/레포명` |
| `infra/argocd.tf` | `repoURL: https://github.com/Jhd1006/ERPulse` | 본인 fork 주소 |
| `manifest/kustomization.yaml` | `images[0].name`의 계정 ID `236510207573` | 본인 AWS 계정 ID (ECR 레지스트리) |

`manifest/kustomization.yaml`의 `newTag` 값은 지금 값 그대로 둬도 됩니다 — 6단계에서 CI가 자동으로 갱신합니다.

## 2. Terraform 변수 준비

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars`에서 채워야 할 값:

- `db_password` — RDS 마스터 비밀번호 (8자 이상)
- `slack_webhook_url` — Alertmanager 알림용 Slack Incoming Webhook URL (필수 변수라 값이 없으면 apply가 실패합니다. Slack 알림이 필요 없다면 더미 URL이라도 넣어두세요)

> **참고**: `terraform.tfvars.example`의 `cluster_version`이 `1.29`로 돼 있는데, `variables.tf`의 기본값과 실제 배포 버전은 `1.36`입니다. apply 전에 원하는 버전으로 맞춰두세요.

### PUBLIC_API_KEY (data.go.kr 공공데이터포털)

`api`가 호출하는 응급의료정보 API(`ErmctInfoInqireService`)는 공공데이터포털 인증키가 필요합니다.

1. [data.go.kr](https://www.data.go.kr) 회원가입/로그인
2. "국립중앙의료원_전국 응급의료기관 정보 조회 서비스" 검색
3. 활용신청 (자동승인이면 즉시, 아니면 심사 후 승인)
4. 마이페이지 → 개발계정 상세보기에서 **일반 인증키(Decoding)** 확인
5. 이 값을 4단계의 k8s Secret에 `PUBLIC_API_KEY`로 등록

### Terraform state 관련 참고

이 프로젝트는 원격 backend(S3 등)를 설정하지 않았습니다 — `terraform.tfstate`는 `apply`를 실행한 로컬 머신에만 남습니다. 혼자 운영하는 포트폴리오 프로젝트라 의도적으로 이렇게 뒀습니다. 팀으로 협업한다면 S3 backend 추가를 고려하세요.

## 3. 인프라 프로비저닝

```bash
terraform init
terraform plan
terraform apply
```

VPC, EKS 클러스터, 노드 그룹, RDS, ECR, ArgoCD(Helm), Cluster Autoscaler, kube-prometheus-stack까지 한 번에 생성됩니다. 완료까지 15~20분 정도 걸립니다.

apply가 끝나면 출력되는 `github_actions_role_arn` 값을 기록해두세요 (다음 단계에서 사용).

## 4. GitHub Actions 연동

CI(`​.github/workflows/ci.yml`)가 ECR에 이미지를 푸시하려면 GitHub OIDC로 발급받은 IAM Role ARN이 필요합니다.

1. fork한 레포 → **Settings → Secrets and variables → Actions**
2. **New repository secret** 클릭
3. Name: `AWS_ROLE_ARN`, Value: 3단계에서 기록한 `github_actions_role_arn` 값 입력

## 5. kubectl 연결

```bash
aws eks update-kubeconfig --name erpulse-cluster --region ap-northeast-2
kubectl get nodes
```

## 6. Kubernetes Secret 수동 적용

`manifest/secret.yaml`은 실제 값이 담기기 때문에 git에 커밋하지 않고(`.gitignore`에 등록됨) 수동으로 클러스터에 적용해야 합니다. `manifest/examples/secret.example.yaml`을 참고해서 값을 채우세요.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: erpulse-api-secret
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://<db_username>:<db_password>@<rds-endpoint>:5432/erpulse"
  REDIS_URL: "redis://redis:6379"
  PUBLIC_API_KEY: "<2단계에서 발급받은 키>"
```

RDS 엔드포인트는 `terraform output`(또는 AWS 콘솔의 RDS 인스턴스)에서 확인할 수 있습니다.

```bash
kubectl apply -f manifest/secret.yaml
```

## 7. DB 마이그레이션 (Alembic)

RDS에 스키마가 아직 없는 상태이므로, API 파드가 뜬 뒤(또는 뜨기 전이라도 DB에 직접 접속 가능하면) 마이그레이션을 적용해야 합니다.

```bash
kubectl exec -it deploy/erpulse-api -- alembic upgrade head
```

> 파드가 아직 없다면 8단계로 먼저 이미지를 배포한 뒤 이 단계를 진행하세요.

## 8. 최초 이미지 빌드 (수동 트리거 필수)

CI는 `api/**` 경로에 변경이 있어야만 자동으로 빌드/푸시합니다. 이 레포를 처음 fork한 시점에는 `api/` 변경이 없으므로 **자동으로 이미지가 만들어지지 않습니다.** GitHub Actions 탭에서 수동으로 한 번 실행해줘야 합니다.

1. fork한 레포 → **Actions** 탭 → **CI** 워크플로우 선택
2. **Run workflow** 버튼 → 브랜치 `main` 선택 → 실행

이 실행이 끝나면:
- ECR에 새 이미지가 푸시되고
- `manifest/kustomization.yaml`의 `newTag`를 갱신하는 커밋이 자동으로 push됩니다

## 9. ArgoCD 배포 확인

ArgoCD는 git을 주기적으로 폴링합니다(기본 3분 간격). 새 커밋을 감지하면 자동 동기화됩니다.

```bash
kubectl get application erpulse-api -n argocd
kubectl get pods
```

`SYNC STATUS: Synced`, `HEALTH STATUS: Healthy`, 파드가 `Running`이면 정상입니다. 바로 확인하고 싶다면:

```bash
kubectl annotate application erpulse-api -n argocd argocd.argoproj.io/refresh=hard --overwrite
```

## 10. 로컬에서 API만 띄워보기 (선택)

AWS 인프라 전체 없이 API 코드만 로컬에서 개발/테스트하려면:

```bash
cd api
cp .env.example .env   # DATABASE_URL, PUBLIC_API_KEY 등 값 채우기
docker compose up
```

테스트 실행:

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/ -v
```

## 11. 정리 (비용 방지)

다 확인했으면 AWS 과금을 막기 위해 리소스를 정리하세요.

```bash
cd infra
terraform destroy
```

ArgoCD가 만든 LoadBalancer 타입 Service는 Terraform이 직접 관리하지 않아서 먼저 지우지 않으면 VPC 삭제가 막힐 수 있는데, `argocd.tf`의 destroy-time provisioner가 `destroy` 실행 시 자동으로 해당 Service를 먼저 삭제하도록 처리되어 있습니다.

---

## 문제가 생겼다면

- **파드가 `ImagePullBackOff`**: ECR에 해당 태그의 이미지가 실제로 있는지 확인 (`aws ecr describe-images --repository-name erpulse-api`). 없다면 8단계를 다시 실행하세요.
- **GitHub Actions가 AWS 인증 실패**: 1단계의 `github_oidc.tf` repo 경로와 4단계의 `AWS_ROLE_ARN` secret 값을 다시 확인하세요.
- **ArgoCD가 `Degraded`인데 파드는 정상**: `kubectl describe application erpulse-api -n argocd`로 실제 원인을 확인하세요. 이미지 문제가 아니라 헬스체크(`/health`) 응답 지연일 수도 있습니다.
