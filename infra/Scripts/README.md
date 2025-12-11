# Domain Monitoring DevOps Infrastructure Setup

This repository contains Bash scripts to automate the setup, deployment, and teardown of a domain monitoring DevOps infrastructure using **Terraform**, **Ansible**, and **AWS**.  

The scripts handle everything from installing required tools, configuring AWS credentials, provisioning infrastructure, copying SSH keys, running Ansible playbooks, and cleaning up resources.

---

## Scripts Overview

---

### 1. `setup_infra.sh`

This is the main setup script that automates the full infrastructure setup. It performs six steps:

1. **Verify and install prerequisites**

   * Checks for **Python3**, **pip3**, **boto3**, **botocore**, **Git**, **Terraform**, and **Ansible**.
   * Automatically installs any missing dependencies.

2. **AWS credentials configuration**

   * Checks for the file `~/.aws/credentials`.
   * If it doesn’t exist, prompts for AWS Access Key ID and Secret Access Key, creates the credentials file, and sets secure permissions (400).

3. **Terraform folder validation**

   * Ensures that the Terraform directories exist:

     * `Terraform/remote-tfstate-bucket`
     * `Terraform/environment`
   * Ensures `main.tf` exists in both directories.

4. **Terraform execution**

   * Runs `terraform init`, `terraform validate`, and `terraform apply --auto-approve` in the remote state bucket and environment directories to provision AWS resources.

5. **SSH key handling**

   * Copies your private key (`group2_private_key.pem`) to `$HOME/.ssh/keys/` and sets secure permissions (400).

6. **Ansible playbook execution**

   * Checks for the Ansible playbook and inventory file.
   * Installs required Ansible Galaxy roles if `requirements.yml` is present.
   * Runs the playbook against the AWS EC2 inventory.

**To run it:**

```bash
chmod +x setup_infra.sh
./setup_infra.sh
```

You can resume from a specific step by passing the step number as an argument:

```bash
./setup_infra.sh 3  # Resume from Step 3
```

---

### 2. `destroy_infra.sh`

This script safely destroys the full infrastructure and optionally cleans up credentials and the Terraform state bucket.

Steps performed:

1. **Validate Terraform** – runs `terraform init` and `terraform validate` in the environment directory.
2. **Destroy Terraform resources** – executes `terraform destroy --auto-approve` to remove all provisioned resources.
3. **Optional Terraform state bucket destruction** – prompts to destroy the remote state bucket and DynamoDB table.
4. **Remove SSH private key** – deletes `group2_private_key.pem` from `$HOME/.ssh/keys/`.
5. **Optional AWS credentials cleanup** – prompts to delete `~/.aws/credentials`.

**To run it:**

```bash
chmod +x destroy_infra.sh
./destroy_infra.sh
```

---

### 3. `destroy_tfstate.sh`

This script is focused on destroying only the Terraform remote state bucket and its locking table without touching the full environment.

Steps performed:

1. Initializes Terraform in the remote state bucket directory.
2. Imports the S3 bucket (`terraform_state`) and DynamoDB table (`terraform_locks`).
3. Applies Terraform to sync the state.
4. Validates and destroys the remote state resources.

**To run it:**

```bash
chmod +x destroy_tfstate.sh
./destroy_tfstate.sh
```

---

### Notes and Requirements

* All scripts are intended for Linux (Ubuntu/Debian recommended).
* They require internet access to install dependencies and clone the Git repository.
* An AWS account and access keys are needed.
* GitHub access is required to clone the project repository.
* Scripts optionally use `set -e` to stop on errors.
* AWS credentials and SSH keys are stored with secure permissions.

---

In short:

* `setup_infra.sh` → sets up the full environment.
* `destroy_infra.sh` → destroys everything including optional cleanup of credentials and SSH keys.
* `destroy_tfstate.sh` → destroys only the Terraform state bucket and locking table.
 
---
