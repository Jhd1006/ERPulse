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