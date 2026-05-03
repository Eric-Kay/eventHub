terraform {
  required_version = ">= 1.6.0"

  backend "s3" {
    bucket         = "eventhub-tf-state-eric-kay"
    key            = "eventhub/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "eventhub-tf-locks"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  name = "${var.project_name}-${var.environment}"

  app_repositories = [
    "frontend",
    "auth-service",
    "event-service",
    "booking-service",
    "payment-service",
    "ticket-service",
    "notification-service",
    "analytics-service"
  ]
}

module "vpc" {
  source = "../../modules/vpc"

  name               = local.name
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

module "eks" {
  source = "../../modules/eks"

  cluster_name        = local.name
  kubernetes_version  = var.kubernetes_version
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_instance_types = var.node_instance_types
  desired_size        = var.desired_size
  min_size            = var.min_size
  max_size            = var.max_size
}

module "ecr" {
  source = "../../modules/ecr"

  repositories = local.app_repositories
  environment  = var.environment
}