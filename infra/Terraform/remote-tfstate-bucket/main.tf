terraform {
  #############################################################
  ## Bootstrapping Process: 
  ## First, run with local backend to create the AWS resources 
  ## required for a remote backend.
  ## Then switch to remote backend by uncommenting the backend 
  ## block below and running terraform init again.
  #############################################################
#  backend "s3" {
#     bucket         = "group2-terraform-bucket-2025-774411"
#     key            = "terraform.tfstate"
#     region         = "us-east-2"
#     dynamodb_table = "group2-terraform-state-locking"
#     encrypt        = true
#  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket        = "group2-terraform-bucket-2025-774411"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "terraform_bucket_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "group2-terraform-state-locking"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  attribute {
    name = "LockID"
    type = "S"
  }
}