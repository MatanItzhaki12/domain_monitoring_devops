
#!/bin/bash
#
# This script performs the first step of the infrastructure setup process.
# It verifies that Python, Terraform, and Ansible are installed on the system.
# If missing, the script installs them automatically.
#
# Tools Checked:
#   - Python3
#   - Terraform 
#   - Ansible
#
# This script is intended to run on a Linux environment.
# It stops execution immediately if any command fails (set -e).
#
# After completing Step 1, the system will be ready for the next phases:

# AWS credentials setup 
# Terraform execution 
# SSH key handling 
# Ansible deployment

set -e

echo " Infra Setup Script -- Starting Execution "
sleep 1

check_installations() {
    echo "----------STEP 1-----------"
    echo "Checking Python, Terraform, and Ansible installations"

    # Python
    if command -v python3 >/dev/null 2>&1; then
        echo "Python3 is installed."
    else
        echo "Python3 not found. Installing Python.."
        sudo apt update
        sudo apt install -y python3
    fi

    # Terraform
    if command -v terraform >/dev/null 2>&1; then
        echo "Terraform is installed."
    else
        echo "Terraform not found. Installing Terraform.."
        sudo apt update
        sudo apt-get install -y gnupg software-properties-common
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update
        sudo apt install -y terraform
    fi

    # Ansible
    if command -v ansible >/dev/null 2>&1; then
        echo "Ansible is installed."
    else
        echo "Ansible not found. Installing Ansible.. "
        sudo apt update
        sudo apt install -y ansible
    fi

    echo "Step 1 is Completed."
}

# This step verifies that the AWS credentials file exists on the system.
# If the file ~/.aws/credentials does not exist, the script prompts the user
# to enter an AWS Access Key ID and Secret Access Key, creates the directory
# structure, generates the credentials file in the required format, and sets
# secure file permissions (chmod 400).
#
# File created:
#   ~/.aws/credentials
#
# Format:
#   [default]
#   aws_access_key_id=YOUR_KEY
#   aws_secret_access_key=YOUR_SECRET
#
# Step 2 ensures Terraform&Ansible can authenticate against AWS in later phases of the infrastructure setup.

check_aws_credentials() {
    echo "----------STEP 2-----------"
    echo "Checking AWS credentials file"

    AWS_DIR="$HOME/.aws"
    CRED_FILE="$AWS_DIR/credentials"

    if [ -f "$CRED_FILE" ]; then
        echo "AWS credentials file already exists at: $CRED_FILE"
    else
        echo "AWS credentials file not found."
        echo "Creating AWS credentials file in: $CRED_FILE"
        echo

        # Ensure the directory exists
        mkdir -p "$AWS_DIR"

        echo "Please enter your AWS credentials (values without quotes):"
        read -r -p "AWS Access Key ID: " AWS_ACCESS_KEY_ID
        read -r -s -p "AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
        echo

        # Create the credentials file
        cat > "$CRED_FILE" <<EOF
[default]
aws_access_key_id=${AWS_ACCESS_KEY_ID}
aws_secret_access_key=${AWS_SECRET_ACCESS_KEY}
EOF

        # Set file permissions to read-only for the user
        chmod 400 "$CRED_FILE"

        echo "AWS credentials file created successfully at: $CRED_FILE"
        echo "File permissions set to 400 (read-only for owner)."
    fi

    echo "Step 2 is Completed."
    
                        }
# This step verifies that the Terraform folder structure required for the
# infrastructure setup exists and is valid.

check_terraform_structure() {
    echo "----------STEP 3-----------"
    echo "Verifying Terraform folder structure and main.tf files"

    PROJECT_ROOT="./domain_monitoring_system"
    INFRA_TF_DIR="$PROJECT_ROOT/Infra/Terraform"
    REMOTE_DIR="$INFRA_TF_DIR/remote-tfstate-bucket"
    ENV_DIR="$INFRA_TF_DIR/environment"

    # Check base Terraform directory
    if [ ! -d "$INFRA_TF_DIR" ]; then
        echo "ERROR: Base Terraform directory not found: $INFRA_TF_DIR"
        exit 1
    fi

    # Array of directories to validate
    for dir in "$REMOTE_DIR" "$ENV_DIR"; do
        if [ ! -d "$dir" ]; then
            echo "ERROR: Terraform directory not found: $dir"
            exit 1
        fi

        if [ ! -f "$dir/main.tf" ]; then
            echo "ERROR: main.tf file not found in directory: $dir"
            exit 1
        fi
    done

    echo "Terraform folder structure and main.tf files are valid- Step 3 is completed."
                            }
check_installations
check_aws_credentials
check_terraform_structure
