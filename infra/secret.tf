# ===== erpulse-api Kubernetes Secret =====

resource "kubernetes_secret" "erpulse_api" {
  metadata {
    name      = "erpulse-api-secret"
    namespace = "default"
  }

  type = "Opaque"

  data = {
    DATABASE_URL   = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/${var.db_name}"
    REDIS_URL      = "redis://redis:6379"
    PUBLIC_API_KEY = var.public_api_key
  }

  depends_on = [aws_eks_node_group.main]
}
