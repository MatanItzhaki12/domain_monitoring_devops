# EC2 Instances

resource "aws_instance" "group2_client_fe" {
    count = var.fe_machines
    ami = var.os_ami
    instance_type = var.ec2_type
    subnet_id = aws_subnet.public.id
    private_ip = cidrhost(var.public_subnet_cidr, 5 + count.index)
    key_name = aws_key_pair.group2_client_public_key.key_name
    vpc_security_group_ids = [aws_security_group.group2_client_fe_security_group.id]
    associate_public_ip_address = false
    tags = {
        Purpose = "FE_EC2_${count.index + 1}"
        Environment = "${var.environment}"
        Group = "${var.group_name}" 
    }
}   

resource "aws_instance" "group2_client_be" {
    count = var.be_machines
    ami = var.os_ami
    instance_type = var.ec2_type
    subnet_id = aws_subnet.private.id
    private_ip = cidrhost(var.private_subnet_cidr, 5 + count.index)
    key_name = aws_key_pair.group2_client_public_key.key_name
    vpc_security_group_ids = [aws_security_group.group2_client_be_security_group.id]
    associate_public_ip_address = false
    tags = {
        Purpose = "BE_EC2_${count.index + 1}"
        Environment = "${var.environment}"
        Group = "${var.group_name}" 
    }
}     