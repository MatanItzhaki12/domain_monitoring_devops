#!/bin/bash
#
# STEP 1:
# Verifies that Python, Terraform, and Ansible are installed on the system.
# If missing, the script installs them automatically.
#
# Tools Checked: (Python, Terraform, Ansible)
#
# It is intended to run on a Linux environment.
# It stops execution immediately if any command fails (set -e).
#
# After completing Step 1, the system will be ready for the next phases:
# AWS credentials setup 
# Terraform execution 
# SSH key handling 
# Ansible deployment
set -e

# The user can choose to start from a different step, by passing it
# like this "./infra_setup.sh 3"
START_STEP=1

# If user passes a step number as argument, use it
if [ $# -eq 1 ]; then
    START_STEP=$1
    echo "Resuming from Step $START_STEP..."
fi

PROJECT_ROOT="$HOME/domain_monitoring_devops_infra/infra"

echo " Infra Setup Script -- Starting Execution "
sleep 1

check_installations() {
    echo "----------STEP 1-----------"
    echo "Checking Python, Terraform, and Ansible installations and downloding the project from git"

    # apt update
    echo "Updating apt packages."
    sudo apt update &>/dev/null

    # Python
    if command -v python3 >/dev/null 2>&1; then
        echo "Python3 is installed."
    else
        echo "Python3 not found. Installing Python..."
        sudo apt install -y python3 &>/dev/null
    fi

    # Ensure pip is installed
    if command -v pip3 >/dev/null 2>&1; then
        echo "pip3 is installed."
    else
        echo "pip3 not found. Installing pip3..."
        sudo apt install -y python3-pip &>/dev/null
    fi

    # Check if boto3 is installed
    if python3 -c "import boto3" >/dev/null 2>&1; then
        echo "boto3 is installed."
    else
        echo "boto3 not found. Installing..."
        sudo apt install -y python3-boto3 &>/dev/null
    fi

    # Check if botocore is installed
    if python3 -c "import botocore" >/dev/null 2>&1; then
        echo "botocore is installed."
    else
        echo "botocore not found. Installing..."
        sudo apt install -y python3-botocore &>/dev/null
    fi
    
    # Upgrade modules, if needed
    python3 -m pip install --user --upgrade boto3 botocore --break-system-packages &>/dev/null

    # # Install boto3 and botocore for AWS Ansible modules
    # echo "Installing boto3 and botocore for Ansible AWS integration..."
    # sudo apt install -y python3-boto3 python3-botocore >/dev/null

    # git
    if command -v git >/dev/null 2>&1; then
        echo "Git is installed."
    else
        echo "Git not found. Installing Git..."
        sudo apt install -y git &>/dev/null
    fi

    # Terraform
    if command -v terraform >/dev/null 2>&1; then
        echo "Terraform is installed."
    else
        echo "Terraform not found. Installing Terraform..."
        sudo apt-get install -y gnupg software-properties-common &>/dev/null
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp.gpg &>/dev/null
        echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main"\
        | sudo tee /etc/apt/sources.list.d/hashicorp.list &>/dev/null
        sudo apt update &>/dev/null
        sudo apt install -y terraform >/dev/null
    fi

    # Ansible
    if command -v ansible >/dev/null 2>&1; then
        echo "Ansible is installed."
    else
        echo "Ansible not found. Installing Ansible..."
        python3 -m pip install --user --upgrade ansible &>/dev/null
    fi

    cd ~

    # Remove existing folder if it exists 
    if [ -d "$HOME/domain_monitoring_devops_infra" ]; then
        echo "Removing existing folder: $HOME/domain_monitoring_devops_infra"
        rm -rf "$HOME/domain_monitoring_devops_infra"
    fi
    
    # Clone the repo
    echo "Cloning project repo (branch: infra)..."
    git clone \
    --branch infra \
    --single-branch \
    https://github.com/MatanItzhaki12/domain_monitoring_devops.git \
    "$HOME/domain_monitoring_devops_infra" &>/dev/null

    PROJECT_ROOT="$HOME/domain_monitoring_devops_infra/infra"
    cd "$PROJECT_ROOT"

    echo "Step 1 is Completed"
}

# STEP 2:
# Verifies that the AWS credentials file exists on the system.
# If the file ~/.aws/credentials does not exist, the script prompts the user
# to enter an AWS Access Key ID and Secret Access Key, creates the directory
# structure, generates the credentials file in the required format, and sets
# secure file permissions.
#
# File created:
#   ~/.aws/credentials
#
# Format:
#   [default]
#   aws_access_key_id=YOUR_KEY
#   aws_secret_access_key=YOUR_SECRET

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
        # `
        # Set file permissions to read-only for the user
        chmod 400 "$CRED_FILE"

        echo "AWS credentials file created successfully at: $CRED_FILE"
        echo "File permissions set to 400 (read-only for owner)."
    fi

    echo "Step 2 is Completed"
}

# STEP 3:
# Verifies that the Terraform folder structure required for the infrastructure setup exists and is valid.

check_terraform_structure() {
    echo "----------STEP 3-----------"
    echo "Verifying Terraform folder structure and main.tf files"

    INFRA_TF_DIR="$PROJECT_ROOT/Terraform"
    REMOTE_DIR="$INFRA_TF_DIR/remote-tfstate-bucket"
    ENV_DIR="$INFRA_TF_DIR/environment"

    # Check base Terraform directory
    if [ ! -d "$INFRA_TF_DIR" ]; then
        echo "ERROR: Base Terraform directory not found: $INFRA_TF_DIR" >&2
        exit 1
    fi

    # Array of directories to validate
    for dir in "$REMOTE_DIR" "$ENV_DIR"; do
        if [ ! -d "$dir" ]; then
            echo "ERROR: Terraform directory not found: $dir" >&2
            exit 1
        fi

        if [ ! -f "$dir/main.tf" ]; then
            echo "ERROR: main.tf file not found in directory: $dir" >&2
            exit 1
        fi
    done

    echo "Terraform folder structure and main.tf files are valid"
    echo "Step 3 is completed"
}

# STEP 4:
# Runs Terraform in the required directories to provision the infrastructure resources.

run_terraform() {
    echo "----------STEP 4-----------"
    echo "Running Terraform in required directories"

    INFRA_TF_DIR="$PROJECT_ROOT/Terraform"
    REMOTE_DIR="$INFRA_TF_DIR/remote-tfstate-bucket"
    ENV_DIR="$INFRA_TF_DIR/environment"

    # Run Terraform in remote-tfstate-bucket
    echo "-> Executing Terraform in: $REMOTE_DIR"
    cd "$REMOTE_DIR"

    # Apply Terraform for remote-tfstate-bucket
    echo "-> Applying Terraform in: $REMOTE_DIR"
        
    terraform init
    terraform validate
    terraform apply --auto-approve
    
    echo ""
    echo "Terraform apply completed for remote-tfstate-bucket."
    echo ""
    
    # Run Terraform in environment
    echo "-> Executing Terraform in: $ENV_DIR"
    cd "$ENV_DIR"

    # Apply Terraform for full environment
    echo "-> Applying Terraform in: $ENV_DIR"

    terraform init
    terraform validate
    terraform apply --auto-approve

    echo ""
    echo "Terraform apply completed for environment."
    echo "STEP 4 is Completed"
}

# STEP 5:
# Copies an existing SSH private key (.pem) provided by the user into: $HOME/.ssh/keys/

copy_ssh_key() {
    echo "----------STEP 5-----------"
    echo "Copying SSH key to $HOME/.ssh/keys/"

    SSH_KEYS_DIR="$HOME/.ssh/keys"
    SRC_KEY="$PROJECT_ROOT/Terraform/environment/keys/group2_private_key.pem"

    if [ ! -f "$SRC_KEY" ]; then
        echo "ERROR: The file '$SRC_KEY' does not exist." >&2
        exit 1
    fi

    # Ensure target directory exists
    mkdir -p "$SSH_KEYS_DIR"

    DEST_KEY="$SSH_KEYS_DIR/$(basename "$SRC_KEY")"
    
    # Check if a key exist, and remove it:
    if [ -f "$DEST_KEY" ]; then
        rm -f "$DEST_KEY"
    fi

    # Copy the key
    cp "$SRC_KEY" "$DEST_KEY"

    # Set secure permissions
    chmod 400 "$DEST_KEY"

    echo "SSH key copied to: $DEST_KEY"
    echo "Permissions set to 400 on copied .pem file."
    echo "STEP 5 is Completed"
}

# Step 6:
# Verifies that the Ansible playbook exists and then runs it

run_ansible_playbook() {
    echo "----------STEP 6-----------"
    echo "Running Ansible playbook"


    ANSIBLE_DIR="$PROJECT_ROOT/Ansible"
    PLAYBOOK_FILE="$ANSIBLE_DIR/playbook.yaml"
    REQUIREMENTS_FILE="$ANSIBLE_DIR/requirements.yml"
    INVENTORY_DIR="$ANSIBLE_DIR/inventory"
    INVENTORY_FILE="$INVENTORY_DIR/aws_ec2.yml"

    # Check that Ansible directory exists
    if [ ! -d "$ANSIBLE_DIR" ]; then
        echo "ERROR: Ansible directory not found: $ANSIBLE_DIR" >&2
        exit 1
    fi

    # Check that playbook file exists
    if [ ! -f "$PLAYBOOK_FILE" ]; then
        echo "ERROR: Ansible playbook not found: $PLAYBOOK_FILE" >&2
        exit 1
    fi

    cd "$ANSIBLE_DIR"

    # If requirements.yml exists, install roles
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo "requirements.yml found. Installing Ansible plugins..."
        ansible-galaxy install -r "$REQUIREMENTS_FILE" &>/dev/null
    else
        echo "No requirements.yml file found. Skipping Ansible Galaxy roles installation."
    fi

    # Check inventory file
    if [ -f "$INVENTORY_FILE" ]; then
        echo "Inventory file found. Running Ansible playbook..."
        ansible-playbook "$(basename "$PLAYBOOK_FILE")" -i "$INVENTORY_FILE" --ask-vault-pass
    else
        echo "ERROR: Inventory file not found at: $INVENTORY_FILE" >&2
        exit 1
    fi

    echo "STEP 6 is Completed"
}

# Calling functions:

# Conditional execution based on START_STEP
if [ "$START_STEP" -le 1 ]; then
    # Step 1
    check_installations
fi

if [ "$START_STEP" -le 2 ]; then
    # Step 2
    check_aws_credentials
fi

if [ "$START_STEP" -le 3 ]; then
    # Step 3
    check_terraform_structure
fi

if [ "$START_STEP" -le 4 ]; then
    # Step 4
    run_terraform
fi

if [ "$START_STEP" -le 5 ]; then
    # Step 5
    copy_ssh_key
fi

if [ "$START_STEP" -le 6 ]; then
    # Step 6
    run_ansible_playbook
fi

echo "Script execution completed."