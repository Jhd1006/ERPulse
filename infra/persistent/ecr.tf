# ===== ECR Repository =====

# 도커 이미지 저장소 생성, mutability => lates 태그 덮어씀
resource "aws_ecr_repository" "main" {
  name                 = var.ecr_repository_name
  image_tag_mutability = var.ecr_image_tag_mutability
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true  # 이미지 푸시 시 보안 스캔
  }

  tags = {
    Name = "erpulse-ecr"
  }
}

# ===== ECR Lifecycle Policy =====
# 최근 10개 이미지까지만 저장, 나머지는 삭제 

resource "aws_ecr_lifecycle_policy" "main" {
  repository = aws_ecr_repository.main.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus     = "any"
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}