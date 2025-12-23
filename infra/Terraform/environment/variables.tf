# environment

variable "group_name" {
    description = "the prefix for the resources of group2"
    type = string
}   

variable "environment" {
    description = "the name of the client"
    type = string
}


# networking

variable "vpc_cidr" {
    description = "the CIDR block for the VPC"
    type = string
}

variable "public_subnet_cidr" {
    description = "the CIDR block for the public subnet"
    type = string
}

variable "private_subnet_cidr" {
    description = "the CIDR block for the private subnet"
    type = string
}


variable "enable_dns_hostnames" {
    description = "Enable DNS hostnames for the VPC"
    type = bool 
    default = true
}

variable "enable_dns_support" {
    description = "Enable DNS support for the VPC"
    type = bool 
    default = true
}

# security

variable "ssh_public_key_name" {
    description = "the name of the public key on aws"
    type = string
}

variable "ssh_private_key_name" {
    description = "the name of the public key on aws"
    type = string
}

# compute

variable "os_ami" {
    description = "the ami of the ec2 instance os"
    type = string
}

variable "ec2_type" {
    description = "the type of the ec2 instance"
    type = string
}

variable "fe_machines" {
    description = "Number of FE instances"
    type = number
}

variable "be_machines" {
    description = "Number of BE instances"
    type = number
    default = 1
}