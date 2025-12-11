resource "aws_instance" "group2-backend" {
  ami = var.os_ami
  instance_type = var.ec2_type
  subnet_id = aws_subnet.public.id
  private_ip    = var.backend_private_ip
  key_name = aws_key_pair.group2_tf_public_key.key_name
  vpc_security_group_ids = [aws_security_group.group2_tf_security_group.id]
  tags = {
    Name = "${var.group_name}-backend"
    Purpose = "backend"
  }
}
