# ===== VPC =====
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "erpulse-vpc"
  }
}

# ===== Internet Gateway =====
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "erpulse-igw"
  }
}

# ===== Public Subnet 1 (워커 노드용) =====
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "erpulse-public-1"
  }
}

# ===== Public Subnet 2 =====
resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "erpulse-public-2"
  }
}

# ===== Private Subnet (RDS용) =====
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.10.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "erpulse-private-1"
  }
}

resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = {
    Name = "erpulse-private-2"
  }
}

# ===== Route Table (Public) =====
# 0.0.0.0의 모든 트래픽은 igw로

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "erpulse-public-rt"
  }
}

# ===== Route Table Association =====
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# ===== 사용 가능한 AZ 가져오기 =====
data "aws_availability_zones" "available" {
  state = "available"
}

# ===== Security Group (EKS) =====
resource "aws_security_group" "eks" {
  name        = "erpulse-eks-sg"
  description = "Security group for EKS cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # VPC 내부의 트래픽만 허용
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # 모든 트래픽
    cidr_blocks = ["0.0.0.0/0"]  # 모든 아웃바운드 허용
  }

  tags = {
    Name = "erpulse-eks-sg"
  }
}

# ===== Security Group (RDS) =====
resource "aws_security_group" "rds" {
  name        = "erpulse-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]  # EKS에서만 접근
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # 모든 트래픽
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "erpulse-rds-sg"
  }
}

# ===== DB Subnet Group =====
resource "aws_db_subnet_group" "main" {
  name       = "erpulse-db-subnet-group"
  subnet_ids = [aws_subnet.private_1.id, aws_subnet.private_2.id]

  tags = {
    Name = "erpulse-db-subnet-group"
  }
}