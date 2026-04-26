terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket         = "replace-me"
    key            = "eventhub/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "replace-me"
  }
}
provider "aws" { region = var.aws_region }

module "ecr" {
  source = "../../modules/ecr"
  repositories = [
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
