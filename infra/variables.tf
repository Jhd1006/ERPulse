# ========================= AWS 기본 설정 =========================

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-northeast-2"
}

# 개발은 dev, 사전 운영은 staging, 운영은 prod

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ========================= VPC 설정 =========================

# 10.0.0.0/16 => 앞 16bits 고정, 10.0.0.0~ 10.0.255.255

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# ========================= EKS 클러스터 설정 =========================

# 클러스터 이름 : erpulse-cluster

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "erpulse-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.36"
}

# ========================= EKS 워커 노드 설정 =========================

# EC2 인스턴스 default 2개 (worker 노드 2개)

variable "node_group_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}

# 자동 확장 최대 4

variable "node_group_max_size" {
  description = "Maximum number of worker nodes for auto-scaling"
  type        = number
  default     = 4
}

variable "node_instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "t3.medium"
}

# ========================= RDS PostgreSQL 설정 =========================

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "erpulse"
}

# 마스터 사용자 postgres, 콘솔에는 **로 보안

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "postgres"
  sensitive   = true
}

# 비밀번호 8자 미만 시 error_message

variable "db_password" {
  description = "RDS master password (min 8 chars, alphanumeric + special)"
  type        = string
  sensitive   = true
  # validation: terraform apply 할 때 자동 검증
  validation {
    condition     = length(var.db_password) >= 8
    error_message = "DB password must be at least 8 characters long."
  }
}

# RDS 저장소 20GB

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"
}

# ========================= ECR 설정 =========================

variable "ecr_repository_name" {
  description = "ECR repository name"
  type        = string
  default     = "erpulse-api"
}

# MUTABLE : 이미지 태그 덮어쓰기 가능 ("latest"로 사용)
variable "ecr_image_tag_mutability" {
  description = "Whether to allow image tag overwrite"
  type        = string
  default     = "MUTABLE"
}

# ========================= AlertManager용 Slack URL  =========================
variable "slack_webhook_url" {
  description = "Slack Incoming Webhook URL for Alertmanager notifications"
  type        = string
  sensitive   = true
}

# ========================= 인증용 API Key  =========================
variable "public_api_key" {
  description = "공공데이터포털(data.go.kr) 응급의료정보 API 인증키"
  type        = string
  sensitive   = true
}
