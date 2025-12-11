#!/bin/bash
read -p "Do you want to use 'set -e' option (Stop when command fail)? (Y/N): " SET_E
if [[ "$SET_E" == "Y" ]]; then
    set -e
fi
# ---------- CONFIGURATION ----------
PROJECT_ROOT="$HOME/domain_monitoring_devops_infra/infra"
PROJECT_TFSTATE_PATH="$PROJECT_ROOT/Terraform/remote-tfstate-bucket"
ENV_DIR="$PROJECT_ROOT/Terraform/environment"
SSH_KEYS_DIR="$HOME/.ssh/keys"
PRIVATE_KEY_NAME="group2_private_key.pem"
AWS_CRED_FILE="$HOME/.aws/credentials"


# ---------- STEP 1: Validate Terraform ----------
echo "---------- STEP 1: Validating Terraform ----------"
cd "$ENV_DIR" 

terraform init
terraform validate

# ---------- STEP 2: Destroy Terraform resources safely ----------
echo "---------- STEP 2: Destroying Terraform Resources ----------"
terraform destroy --auto-approve
echo -e "\n"

# -------- STEP 3: Prompt for TF state bucket destruction --------
read -p "Do you want to destroy the Terraform state bucket? (Y/N): " DESTROY_BUCKET
if [[ "$DESTROY_BUCKET" == "Y" ]]; then
    echo "---------- STEP 3: Destroying Terraform state bucket ----------"
    cd "$PROJECT_TFSTATE_PATH" 

    terraform init 

    terraform import aws_s3_bucket.terraform_state group2-terraform-bucket-2025-774411 &>/dev/null
    terraform import aws_dynamodb_table.terraform_locks group2-terraform-state-locking &>/dev/null
    
    terraform validate &>/dev/null
    terraform apply --auto-approve &>/dev/null

    echo -e "\n"

    terraform validate
    terraform destroy --auto-approve 
else
    echo "Terraform state bucket destruction skipped."
fi

# ---------- STEP 4: Remove private SSH key ----------
KEY_PATH="$SSH_KEYS_DIR/$PRIVATE_KEY_NAME"
if [ -f "$KEY_PATH" ]; then
    echo "---------- STEP 4: Removing SSH private key ----------"
    rm -f "$KEY_PATH"
fi

# ---------- STEP 5: Clean up AWS credentials ----------
if [ -f "$AWS_CRED_FILE" ]; then
    read -p "Do you want to remove AWS credentials? (Y/N): " RM_CRED
    if [[ "$RM_CRED" == "Y" ]]; then
        echo "---------- STEP 5: Removing AWS credentials ----------"
        rm -f "$AWS_CRED_FILE"
    fi
fi


echo "---------- DONE: Terraform Environment destroyed and cleanup completed ----------"