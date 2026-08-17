# Terraform state backend.
terraform {
  backend "s3" {
    bucket         = "stratum-terraform-state"
    key            = "stratum/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "stratum-terraform-locks"
  }

  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }
  }
}
