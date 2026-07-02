# ===== RDS PostgreSQL =====
resource "aws_db_instance" "main" {
  identifier     = "erpulse-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class  # db.t3.micro

  db_name  = var.db_name          # erpulse
  username = var.db_username      # postgres
  password = var.db_password      # 실제 암호 (terraform.tfvars에서)

  allocated_storage = var.db_allocated_storage  # 20GB

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot       = true  # destroy 시 스냅샷 생성 안 함 (빠름)
  deletion_protection       = false
  publicly_accessible       = false  # 인터넷 접근 불가
  multi_az                  = false
  backup_retention_period   = 7      # 백업 7일 유지
  backup_window             = "03:00-04:00"  # UTC
  maintenance_window        = "sun:04:00-sun:05:00"

  tags = {
    Name = "erpulse-db"
  }
}
