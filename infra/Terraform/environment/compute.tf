# EC2 Instances

resource "aws_instance" "group2_client_fe" {
    count = var.fe_machines
    ami = var.os_ami
    instance_type = var.ec2_type
    subnet_id = aws_subnet.public_a.id
    private_ip = cidrhost(var.public_subnet_cidr_a, 5 + count.index)
    key_name = aws_key_pair.group2_client_public_key.key_name
    vpc_security_group_ids = [aws_security_group.group2_client_fe_security_group.id]
    associate_public_ip_address = false
    tags = {
        Name = "${var.group_name}-${var.environment}-fe-${count.index + 1}"
        Purpose = "FE_EC2"
        Environment = "${var.environment}"
        Group = "${var.group_name}" 
    }
}   

resource "aws_instance" "group2_client_be" {
    count = var.be_machines
    ami = var.os_ami
    instance_type = var.ec2_type
    subnet_id = aws_subnet.private_a.id
    private_ip = cidrhost(var.private_subnet_cidr_a, 5 + count.index)
    key_name = aws_key_pair.group2_client_public_key.key_name
    vpc_security_group_ids = [aws_security_group.group2_client_be_security_group.id]
    associate_public_ip_address = false
    tags = {
        Name = "${var.group_name}-${var.environment}-be-${count.index + 1}"
        Purpose = "BE_EC2"
        Environment = "${var.environment}"
        Group = "${var.group_name}" 
    }
}     