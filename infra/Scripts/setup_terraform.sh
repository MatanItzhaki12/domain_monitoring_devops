set e 
cd $WORKSPACE/Terraform/environment

echo "Writing Variables to terraform.tfvars"
cat  << EOF > "./terraform.tfvars"
# environment
group_name = "Group2"
environment = ${params.CLIENT_NAME}

# networking
vpc_cidr = "10.11.0.0/16"
public_subnet_cidr = "10.11.1.0/24"
private_subnet_cidr = "10.11.2.0/24"

# security
ssh_public_key_name = "group2_${params.CLIENT_NAME}_dms_pubkey"
ssh_private_key_name = "group2_${params.CLIENT_NAME}_private_key"

# compute
os_ami = "ami-0f5fcdfbd140e4ab7"
ec2_type = "t3.small"
fe_machines = ${params.FRONTEND_VM_COUNT}
be_machines = ${params.BACKEND_VM_COUNT}
EOF

terraform init -input=false
terraform plan -input=false -out=tfplan
terraform apply -input=false tfplan --auto-approve