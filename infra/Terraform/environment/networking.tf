# VPC

resource "aws_vpc" "group2_vpc" {
    cidr_block = var.vpc_cidr
    enable_dns_support = var.enable_dns_support
    enable_dns_hostnames = var.enable_dns_hostnames

    tags = {
        Name = "${var.group_name}_vpc"
    }
}

# PUBLIC SUBNET

resource "aws_subnet" "public" {
    vpc_id = aws_vpc.group2_vpc.id
    cidr_block = var.public_subnet_cidr
    map_public_ip_on_launch = true

    tags = {
        Name = "${var.group_name}_subnet"
    }
}

# INTERNET GATEWAY

resource "aws_internet_gateway" "group2_igw" {
    vpc_id = aws_vpc.group2_vpc.id

    tags = {
        Name = "${var.group_name}_igw"
    }
}

# ROUTE TABLE

resource "aws_route_table" "group2_public_rt" {
    vpc_id = aws_vpc.group2_vpc.id
    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.group2_igw.id
    }

    tags = {
        Name = "${var.group_name}_public_rt"
    }
}

# ROUTE TABLE ASSOCIATION

resource "aws_route_table_association" "group2_rt_association" {
    subnet_id = aws_subnet.public.id
    route_table_id = aws_route_table.group2_public_rt.id
}
