# VPC

resource "aws_vpc" "group2_client_vpc" {
    cidr_block = var.vpc_cidr
    enable_dns_support = var.enable_dns_support
    enable_dns_hostnames = var.enable_dns_hostnames

    tags = {
        Name = "${var.group_name}-${var.environment}-vpc"
        Purpose = "vpc"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
    }
}

# PUBLIC SUBNET

resource "aws_subnet" "public_a" {
    vpc_id = aws_vpc.group2_client_vpc.id
    cidr_block = var.public_subnet_cidr_a
    map_public_ip_on_launch = true
    availability_zone = "us-east-2a" 

    tags = {
        Name = "${var.group_name}-${var.environment}-public-a"
        Purpose = "public_subnet"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
        AZ = "us-east-2a" 
    }
}

resource "aws_subnet" "public_b" {
    vpc_id = aws_vpc.group2_client_vpc.id
    cidr_block = var.public_subnet_cidr_b
    map_public_ip_on_launch = true
    availability_zone = "us-east-2b" 

    tags = {
        Name = "${var.group_name}-${var.environment}-public-b"
        Purpose = "public_subnet"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
        AZ = "us-east-2b" 
    }
}


resource "aws_subnet" "private_a" {
    vpc_id = aws_vpc.group2_client_vpc.id
    cidr_block = var.private_subnet_cidr_a
    map_public_ip_on_launch = false
    availability_zone = "us-east-2a" 

    tags = {
        Name = "${var.group_name}-${var.environment}-private-a"
        Purpose = "private_subnet"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
        AZ = "us-east-2a"
    }
}

resource "aws_subnet" "private_b" {
    vpc_id = aws_vpc.group2_client_vpc.id
    cidr_block = var.private_subnet_cidr_b
    map_public_ip_on_launch = false
    availability_zone = "us-east-2b"

    tags = {
        Name = "${var.group_name}-${var.environment}-private-b"
        Purpose = "private_subnet"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
        AZ = "us-east-2b"
    }
}

# INTERNET GATEWAY

resource "aws_internet_gateway" "group2_client_igw" {
    vpc_id = aws_vpc.group2_client_vpc.id

    tags = {
        Purpose = "igw"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
    }
}

# ROUTE TABLE

resource "aws_route_table" "group2_client_public_rt" {
    vpc_id = aws_vpc.group2_client_vpc.id
    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.group2_client_igw.id
    }

    tags = {
        Purpose = "public_rt"
        Environment = "${var.environment}"
        Group = "${var.group_name}"        
    }
}

# ROUTE TABLE ASSOCIATION

resource "aws_route_table_association" "group2_client_rt_association" {
    subnet_id = aws_subnet.public_a.id
    route_table_id = aws_route_table.group2_client_public_rt.id
}
