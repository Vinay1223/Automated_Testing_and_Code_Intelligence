terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.50" }
  }
}

provider "aws" {
  region = var.region
}

# --- VPC ------------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "codeintel-${var.environment}"
  cidr = "10.30.0.0/16"

  azs             = ["${var.region}a", "${var.region}b"]
  private_subnets = ["10.30.1.0/24", "10.30.2.0/24"]
  public_subnets  = ["10.30.101.0/24", "10.30.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = var.environment != "prod"
}

# --- ECS Fargate API ------------------------------------------------------
resource "aws_ecs_cluster" "this" {
  name = "codeintel-${var.environment}"
}

# --- RDS Postgres ---------------------------------------------------------
resource "aws_db_instance" "postgres" {
  identifier              = "codeintel-${var.environment}"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = var.db_instance_class
  allocated_storage       = 50
  storage_encrypted       = true
  db_name                 = "codeintel"
  username                = "codeintel"
  password                = var.db_password
  skip_final_snapshot     = var.environment != "prod"
  backup_retention_period = var.environment == "prod" ? 14 : 1
  multi_az                = var.environment == "prod"
}

# --- ElastiCache Redis ----------------------------------------------------
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "codeintel-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t4g.small"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
}
