# AWS infrastructure: EKS + RDS + ElastiCache + S3 + Secret Manager.
# Run: terraform init && terraform apply -var-file=environments/prod.tfvars
provider "aws" {
  region = var.region
  default_tags {
    tags = merge({ Project = var.project, Environment = var.environment }, var.tags)
  }
}

# --- VPC -------------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.8.1"

  name = "${var.project}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "production"
  enable_dns_hostnames = true
}

# --- EKS ---------------------------------------------------------------------
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.8.5"

  cluster_name    = var.cluster_name
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = var.environment != "production"

  eks_managed_node_groups = {
    agents = {
      desired_size = 3
      min_size     = 2
      max_size     = 8
      instance_types = ["m6i.large"]
    }
  }
}

# --- RDS PostgreSQL ------------------------------------------------------------
resource "aws_db_subnet_group" "stratum" {
  name       = "${var.project}-db-subnets"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_db_instance" "stratum" {
  identifier     = "${var.project}-db"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = var.db_instance_class

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_encrypted     = true

  db_name  = "stratum"
  username = "agent"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.stratum.name
  vpc_security_group_ids = [aws_security_group.database.id]
  skip_final_snapshot    = false
  backup_retention_period = 30
  multi_az               = var.environment == "production"
}

# --- ElastiCache Redis ---------------------------------------------------------
resource "aws_elasticache_subnet_group" "stratum" {
  name       = "${var.project}-redis-subnets"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "stratum" {
  cluster_id           = "${var.project}-redis"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  subnet_group_name    = aws_elasticache_subnet_group.stratum.name
  security_group_ids   = [aws_security_group.redis.id]
  snapshot_retention_limit = 7
}

# --- S3 (client files, backups, case data) ------------------------------------
resource "aws_s3_bucket" "stratum_files" {
  bucket = "${var.project}-${var.environment}-files"
}

resource "aws_s3_bucket_versioning" "stratum_files" {
  bucket = aws_s3_bucket.stratum_files.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stratum_files" {
  bucket = aws_s3_bucket.stratum_files.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# --- Secrets Manager (API keys per client instance) ----------------------------
resource "aws_secretsmanager_secret" "client_secrets" {
  name_prefix = "${var.project}/client/"
}

# --- Security groups -------------------------------------------------------------
resource "aws_security_group" "database" {
  name   = "${var.project}-db"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}

resource "aws_security_group" "redis" {
  name   = "${var.project}-redis"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port = 6379
    to_port   = 6379
    protocol  = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}
