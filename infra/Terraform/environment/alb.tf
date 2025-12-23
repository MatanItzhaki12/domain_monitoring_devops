# --- FE ALB ---
resource "aws_lb" "group2_client_fe_alb" {
    name = "${group_name}-${environment}-fe-alb"
    load_balancer_type = "application"
    subnets = [aws_subnet.public.id]
    security_groups = [aws_security_group.group2_client_fe_security_group.id]
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
    name = "${group_name}-${environment}-fe-alb-tg"
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
        values = ["*"]
      }
    }
    action {
        type = "forward"
        target_group_arn = aws_lb_target_group.group2_client_fe_alb_tg.arn
    }
}

# --- BE ALB ---
resource "aws_lb" "group2_client_be_alb" {
    name = "${group_name}-${environment}-be-alb"
    load_balancer_type = "application"
    subnets = [aws_subnet.private.id]
    security_groups = [aws_security_group.group2_client_be_security_group.id]
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
    name = "${group_name}-${environment}-be-alb-tg"
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
        values = ["*"]
      }
    }
    action {
        type = "forward"
        target_group_arn = aws_lb_target_group.group2_client_be_alb_tg.arn
    }
}