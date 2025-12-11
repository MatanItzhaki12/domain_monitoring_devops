#!/bin/bash

PROJECT_ROOT="$HOME/domain_monitoring_devops_infra/infra"
PROJECT_TFSTATE_PATH="$PROJECT_ROOT/Terraform/remote-tfstate-bucket"


cd "$PROJECT_TFSTATE_PATH" 

terraform init

terraform import aws_s3_bucket.terraform_state group2-terraform-bucket-2025-774411 &>/dev/null
terraform import aws_dynamodb_table.terraform_locks group2-terraform-state-locking &>/dev/null
terraform apply --auto-approve


terraform validate
terraform destroy --auto-approve