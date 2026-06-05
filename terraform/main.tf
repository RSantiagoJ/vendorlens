terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # S3 remote state — uncomment after bootstrapping the state bucket:
  #   aws s3 mb s3://vendorlens-tfstate-<account_id> --region us-east-1
  # Then run: terraform init -migrate-state
  #
  # backend "s3" {
  #   bucket = "vendorlens-tfstate-<account_id>"
  #   key    = "vendorlens/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
