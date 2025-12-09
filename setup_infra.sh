
#!/bin/bash
#
# Infra Setup Script - Step 1
# ------------------------------------------
# This script performs the first step of the infrastructure setup process.
# It verifies that Python3, Terraform, and Ansible are installed on the system.
# If any of these tools are missing, the script installs them automatically.
#
# Tools Checked:
#   - Python3
#   - Terraform (via HashiCorp official repository)
#   - Ansible
#
# This script is intended to run on a Linux environment (Ubuntu/Debian-based).
# It stops execution immediately if any command fails (set -e).
#
# After completing Step 1, the system will be ready for the next phases:
# AWS credentials setup, Terraform execution, SSH key handling, and Ansible deployment.
#
# Author: Oz Efraty
# Date: 2025

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

check_installations