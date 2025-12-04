# environment
group_name = "Group2"

# networking
vpc_cidr = "10.11.0.0/16"
public_subnet_cidr = "10.11.1.0/24"

# security

ssh_public_key_name = "group2_tf_dms_pubkey"
ssh_private_key_name = "group2_private_key"

# compute
os_ami = "ami-0f5fcdfbd140e4ab7"
ec2_type = "t3.small"
jenkins_master_private_ip = "10.11.1.5"
jenkins_agent_private_ip = "10.11.1.6"