
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

echo " Infra Setup Script -- Starting Execution "
sleep 1

INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$INFRA_DIR"

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

    terraform init
    terraform validate
    terraform apply --auto-approve

    echo "Terraform apply completed for remote-tfstate-bucket."

    # Run Terraform in environment
    echo "-> Executing Terraform in: $ENV_DIR"
    cd "$ENV_DIR"

    terraform init
    terraform validate
    terraform apply --auto-approve

    echo "Terraform apply completed for environment."
    echo "STEP 4 is Completed"
                }

# STEP 5:
# Copies an existing SSH private key (.pem) provided by the user into: $HOME/.ssh/keys/

copy_ssh_key() {
    echo "----------STEP 5-----------"
    echo "Copying SSH key to \$HOME/.ssh/keys/"

    SSH_KEYS_DIR="$HOME/.ssh/keys"

    read -r -p "Enter FULL path to your SSH private key (.pem): " SRC_KEY

    if [ ! -f "$SRC_KEY" ]; then
        echo "ERROR: The file '$SRC_KEY' does not exist."
        exit 1
    fi

    # Ensure target directory exists
    mkdir -p "$SSH_KEYS_DIR"

    DEST_KEY="$SSH_KEYS_DIR/$(basename "$SRC_KEY")"

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
    INVENTORY_FILE="$INVENTORY_DIR/inventory.ini"

    # Check that Ansible directory exists
    if [ ! -d "$ANSIBLE_DIR" ]; then
        echo "ERROR: Ansible directory not found: $ANSIBLE_DIR"
        exit 1
    fi

    # Check that playbook file exists
    if [ ! -f "$PLAYBOOK_FILE" ]; then
        echo "ERROR: Ansible playbook not found: $PLAYBOOK_FILE"
        exit 1
    fi

    cd "$ANSIBLE_DIR"

    # If requirements.yml exists, install roles
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo "requirements.yml found. Installing Ansible roles..."
        ansible-galaxy install -r "$REQUIREMENTS_FILE"
    else
        echo "No requirements.yml file found. Skipping Ansible Galaxy roles installation."
    fi

    # Check inventory file
    if [ -f "$INVENTORY_FILE" ]; then
    echo "Inventory file found. Running Ansible playbook..."
    ansible-playbook "$(basename "$PLAYBOOK_FILE")" -i "$INVENTORY_FILE"
    else
    echo "ERROR: Inventory file not found at: $INVENTORY_FILE"
    exit 1
    fi

    echo "STEP 6 is Completed"
                        }

# Calling functions:

check_installations
check_aws_credentials
check_terraform_structure
run_terraform
copy_ssh_key
run_ansible_playbook