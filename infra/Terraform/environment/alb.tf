# --- FE ALB ---
resource "aws_lb" "group2_client_fe_alb" {
    name = "${var.group_name}-${var.environment}-fe-alb"
    load_balancer_type = "application"
    subnets = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups = [aws_security_group.group2_client_fe_security_group.id]

    tags = {
        Name = "${var.group_name}-${var.environment}-FE-ALB"
        Purpose = "FE_ALB"
        Environment = "${var.environment}"
        Group = "${var.group_name}"
    }
}

resource "aws_lb_listener" "http" {
    load_balancer_arn = aws_lb.group2_client_fe_alb.arn
    port = 80
    protocol = "HTTP"

    default_action {
        type = "fixed-response"

        fixed_response {
            content_type = "text/plain"
            message_body = "404: page not found"
            status_code  = 404            
        }
    }
}

resource "aws_lb_target_group" "group2_client_fe_alb_tg" {
    name = "${var.group_name}-${var.environment}-fe-alb-tg"
    port = 8080
    protocol = "HTTP"
    vpc_id = aws_vpc.group2_client_vpc.id

    stickiness {
        enabled         = true
        type            = "lb_cookie"
        cookie_duration = 86400   # seconds (1 day)
    }

    health_check {
        path = "/health"
        protocol = "HTTP"
        matcher = "200"
        interval = 15
        timeout = 3
        healthy_threshold = 2
        unhealthy_threshold = 2
    }

    tags = {
        Name        = "${var.group_name}-${var.environment}-fe-tg"
        Purpose     = "ALB_FE_TG"
        Environment = var.environment
        Group       = var.group_name
    }
}

resource "aws_lb_target_group_attachment" "group2_client_fe_attach" {
    count = var.fe_machines
    target_group_arn = aws_lb_target_group.group2_client_fe_alb_tg.arn
    target_id = aws_instance.group2_client_fe[count.index].id
    port = 8080
}

resource "aws_lb_listener_rule" "fe-instances" {
    listener_arn = aws_lb_listener.http.arn
    priority = 100
    condition {
      path_pattern {
        values = ["/*"]
      }
    }
    action {
        type = "forward"
        target_group_arn = aws_lb_target_group.group2_client_fe_alb_tg.arn
    }
}

# --- BE ALB ---
resource "aws_lb" "group2_client_be_alb" {
    name = "${var.group_name}-${var.environment}-be-alb"
    load_balancer_type = "application"
    internal = true
    subnets = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups = [aws_security_group.group2_client_be_security_group.id]
    tags = {
        Name = "${var.group_name}-${var.environment}-BE-ALB"
        Purpose = "BE_ALB"
        Environment = "${var.environment}"
        Group = "${var.group_name}"

    }
}

resource "aws_lb_listener" "be_http" {
    load_balancer_arn = aws_lb.group2_client_be_alb.arn
    port = 8080
    protocol = "HTTP"

    default_action {
        type = "fixed-response"

        fixed_response {
            content_type = "text/plain"
            message_body = "404: page not found"
            status_code  = 404            
        }
    }
}

resource "aws_lb_target_group" "group2_client_be_alb_tg" {
    name = "${var.group_name}-${var.environment}-be-alb-tg"
    port = 8080
    protocol = "HTTP"
    vpc_id = aws_vpc.group2_client_vpc.id

    health_check {
        path = "/health"
        protocol = "HTTP"
        matcher = "200"
        interval = 15
        timeout = 3
        healthy_threshold = 2
        unhealthy_threshold = 2
    }

    tags = {
        Name        = "${var.group_name}-${var.environment}-be-tg"
        Purpose     = "ALB_BE_TG"
        Environment = var.environment
        Group       = var.group_name
    }
}

resource "aws_lb_target_group_attachment" "group2_client_be_attach" {
    count = var.be_machines
    target_group_arn = aws_lb_target_group.group2_client_be_alb_tg.arn
    target_id = aws_instance.group2_client_be[count.index].id
    port = 8080
}

resource "aws_lb_listener_rule" "be-instances" {
    listener_arn = aws_lb_listener.be_http.arn
    priority = 100
    condition {
      path_pattern {
        values = ["/*"]
      }
    }
    action {
        type = "forward"
        target_group_arn = aws_lb_target_group.group2_client_be_alb_tg.arn
    }
}