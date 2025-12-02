# EC2 Instances

resource "aws_instance" "group2-jenkins-master" {
    ami = "ami-0f5fcdfbd140e4ab7"
    instance_type = "t3.small"
    subnet_id = aws_subnet.public.id
    key_name = aws_key_pair.group2_tf_public_key.key_name
    vpc_security_group_ids = [aws_security_group.group2_tf_security_group.id]
    tags = {
        Name = "group2-jenkins-master"
    }
}   

resource "aws_instance" "group2-jenkins-agent" {
    ami = "ami-0f5fcdfbd140e4ab7"
    instance_type = "t3.small"
    subnet_id = aws_subnet.public.id
    key_name = aws_key_pair.group2_tf_public_key.key_name
    vpc_security_group_ids = [aws_security_group.group2_tf_security_group.id]
    tags = {
        Name = "group2-jenkins-agent"
    }
}   