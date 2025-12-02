# VPC

resource "aws_vpc" "group2_vpc" {
    cidr_block = "10.11.0.0/16"
    enable_dns_support = true
    enable_dns_hostnames = true

    tags = {
        Name = "group2_vpc"
    }
}

# PUBLIC SUBNET

resource "aws_subnet" "public" {
    vpc_id = aws_vpc.group2_vpc.id
    cidr_block = "10.11.1.0/24"
    map_public_ip_on_launch = true

    tags = {
        Name = "group2_subnet"
    }
}

# INTERNET GATEWAY

resource "aws_internet_gateway" "group2_igw" {
    vpc_id = aws_vpc.group2_vpc.id

    tags = {
        Name = "group2_igw"
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
        Name = "group2_public_rt"
    }
}

# ROUTE TABLE ASSOCIATION

resource "aws_route_table_association" "group2_rt_association" {
    subnet_id = aws_subnet.public.id
    route_table_id = aws_route_table.group2_public_rt.id
}
