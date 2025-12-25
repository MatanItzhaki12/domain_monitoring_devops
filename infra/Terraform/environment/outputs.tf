output "fe_alb_dns_name" {
    description = "the public IP of the FE ALB"
    value = aws_lb.group2_client_fe_alb.dns_name
}

output "be_alb_dns_name" {
    description = "the public IP of the BE ALB"
    value = aws_lb.group2_client_be_alb.dns_name
}