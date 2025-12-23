# environment
group_name = "Group2"
environment = "Client1"

# networking
vpc_cidr = "10.11.0.0/16"
public_subnet_cidr = "10.11.1.0/24"
private_subnet_cidr = "10.11.2.0/24"

# security

ssh_public_key_name = "group2_${environment}_dms_pubkey"
ssh_private_key_name = "group2_${environment}_private_key"

# compute
os_ami = "ami-0f5fcdfbd140e4ab7"
ec2_type = "t3.small"
fe_machines = 3
be_machines = 1
