# Backend Infra (Terraform & Ansible)

This folder provides minimal infrastructure deployment artifacts for the backend service.

Ansible Playbook: `infra/backend/Ansible/playbook.yaml`
- Clones the repository, builds the Docker image using the `backend/Dockerfile` and runs the container.

Terraform: `infra/backend/Terraform/` (backend.tf / variables.tf)
- Minimal example to add a dedicated `group2-backend` EC2 instance.

Notes:
- These files are a starting point and assume the existing Terraform/VPC/subnet resources and variables are available in the `infra/Terraform/environment` folder.
- Adjust variables and networking configuration to match your target environment.
