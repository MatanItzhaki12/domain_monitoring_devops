# Generate SSH key

resource "tls_private_key" "group2_generated_keys" {
    algorithm = "RSA"
    rsa_bits = 4096
}

# Upload public key to AWS

resource "aws_key_pair" "group2_tf_public_key" {
    key_name = var.ssh_public_key_name
    public_key = tls_private_key.group2_generated_keys.public_key_openssh
}

# Save private key locally

resource "local_file" "group2_tf_private_key" {
    content = tls_private_key.group2_generated_keys.private_key_pem
    filename = "${path.root}/keys/${var.ssh_private_key_name}.pem"
    file_permission = "0400"

    # provisioner "local-exec" {
    #     when = create
    #     command = "chmod 400 \"${path.module}/generated_key.pem\""
    # }
}

# Create The Security group

resource "aws_security_group" "group2_tf_security_group" {
    name = "${var.group_name}-TF-SG"
    vpc_id = aws_vpc.group2_vpc.id
    # Inbound Rules
    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }
    ingress {
        from_port = 8080
        to_port = 8080
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    } 
    # Maybe 50000 is not neccassery?    
    ingress {
        from_port = 50000
        to_port = 50000
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Outbound Rule
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
    tags = {
        Name = "${var.group_name}_TF_SG"
    }
}