terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for storing Terraform state
  # Uncomment and configure this if you want to store state in S3
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "llm-analysis-pipeline/terraform.tfstate"
  #   region         = "eu-west-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"  # Optional but recommended for state locking
  # }
}

# Configure AWS Provider
provider "aws" {
  region = "eu-west-1"  # Match your region
  
  # Default tags to be applied to all resources
  default_tags {
    tags = {
      Environment = "dev"
      Project     = "llm-analysis-pipeline"
      ManagedBy   = "terraform"
      Owner       = "your-team"
    }
  }
}

# Optional but helpful for debugging
data "aws_caller_identity" "current" {}

# Output the AWS account ID (helpful for verification)
output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

# Output the AWS region (helpful for verification)
output "aws_region" {
  value = "eu-west-1"
}