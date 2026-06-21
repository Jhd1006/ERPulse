# ERPulse Terraform Infrastructure

## 개요

AWS EKS, RDS, ECR을 Terraform으로 자동 프로비저닝합니다.

## 파일 설명

**main.tf** - AWS 프로바이더 설정. Terraform 1.0 이상, AWS Provider 5.x 필수.

**variables.tf** - 프로젝트 전체 변수 정의. aws_region, cluster_name, db_password 등.

**terraform.tfvars** - 변수값 실제 설정 (로컬만, .gitignore). GitHub에는 terraform.tfvars.example만 올라감.

**vpc.tf** - VPC (10.0.0.0/16), Public/Private Subnet, Internet Gateway, Security Group, Route Table. Public Subnet에 EKS, Private Subnet에 RDS 배치.

**eks.tf** - EKS 클러스터 생성. IAM Role (클러스터용, 노드용), EKS Cluster (1.29), Node Group (desired:2, max:4, t3.medium). OIDC Provider로 ArgoCD 지원.

**rds.tf** - RDS PostgreSQL. db.t3.micro (Free Tier), 20GB, multi_az=true (고가용성), backup_retention=7. Private Subnet에 배치, EKS에서만 접근 가능.

**ecr.tf** - ECR 이미지 저장소. erpulse-api, 최근 10개 이미지 유지, 푸시 시 보안 스캔.

## 사용 방법

```bash
cd infra
terraform init
terraform plan
terraform apply
terraform destroy
```

## 비용

- EKS: $0.10/시간 (항상)
- Worker Node (t3.medium × 2): $60/월
- RDS (db.t3.micro): Free Tier (750시간/월)

## 주의

- terraform.tfvars는 .gitignore에 있어서 Git 제외됨
- destroy 후 재생성 가능 (skip_final_snapshot=true)
- 상태 파일(terraform.tfstate)은 로컬만 유지