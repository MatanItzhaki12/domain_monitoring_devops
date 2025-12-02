# Determine OS

locals {
    is_windows = lower(var.os_type) == "windows"
}

# Generate SSH key

resource "tls_private_key" "group2_generated_keys" {
    algorithm = "RSA"
    rsa_bits = 4096
}

# Upload public key to AWS

resource "aws_key_pair" "group2_tf_public_key" {
    key_name = "group2_tf_dms_pubkey"
    public_key = tls_private_key.group2_generated_keys.public_key_openssh
}

# Save private key locally

resource "local_file" "group2_tf_private_key" {
    content = tls_private_key.group2_generated_keys.private_key_pem
    filename = (
        local.is_windows ? "${path.module}\\generated_key.pem"
        : "${path.module}/generated_key.pem"
    )
    file_permission = local.is_windows ? null : "0400"

    provisioner "local-exec" {
        when = create
        command = (
            local.is_windows ? 
            "attrib +R \"${path.module}\\generated_key.pem\"" :
            "chmod 400 \"${path.module}/generated_key.pem\""
        )
    }
}

# Create The Security group

resource "aws_security_group" "group2_tf_security_group" {
    name = "group2_tf_security_group"
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
        Name = "Group2_TF_SG"
    }
}