# ===== GitHub Actions OIDC Provider =====

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# ===== IAM Role: GitHub Actions가 assume할 역할 =====

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_actions.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # main 브랜치에서 실행되는 워크플로만 이 Role을 assume 가능
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:Jhd1006/ERPulse:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions_ecr" {
  name               = "erpulse-github-actions-ecr"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
}

# ===== IAM Policy: ECR push 권한만 부여 (최소 권한) =====

data "aws_iam_policy_document" "github_actions_ecr_push" {
  statement {
    sid       = "ECRAuth"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]  # GetAuthorizationToken은 리소스 레벨 제한이 불가능한 액션
  }

  statement {
    sid    = "ECRPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]
    resources = [aws_ecr_repository.main.arn]  # erpulse-api 리포지토리로 한정
  }
}

resource "aws_iam_role_policy" "github_actions_ecr_push" {
  name   = "erpulse-github-actions-ecr-push"
  role   = aws_iam_role.github_actions_ecr.id
  policy = data.aws_iam_policy_document.github_actions_ecr_push.json
}

output "github_actions_role_arn" {
  description = "GitHub Actions가 assume할 IAM Role ARN"
  value       = aws_iam_role.github_actions_ecr.arn
}