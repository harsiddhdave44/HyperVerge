terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.0.1"
    }
  }
}

provider "aws" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public.*.id[count.index]
  route_table_id = aws_route_table.public.id
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index].cidr
  availability_zone       = var.public_subnet_cidrs[count.index].az
  map_public_ip_on_launch = true
}

# Defining the ingress ports for SSH(22), http(80) and for the js script(81)
resource "aws_security_group" "elb" {
  name        = "elb"
  description = "Allow inbound traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 81
    to_port     = 81
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "web" {
  name               = "web-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.elb.id]
  subnets            = aws_subnet.public.*.id

}

resource "aws_lb_target_group" "front_end" {
  name     = "front-end"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
}

resource "aws_lb_listener" "front_end" {
  load_balancer_arn = aws_lb.web.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.front_end.arn
  }
}


resource "aws_launch_configuration" "web" {
  name          = "web-lc"
  image_id      = var.ami
  instance_type = var.instance_type
  key_name      = "key_par_tf" # This must be created manually first

  # This user data install nodejs, npm and pm2. 
  # Then it creates a node script which prints the Instance ID, IP Address and MAC(on port 81) 
  # Another server acts as a health check(on port 80) 
  # Kept two separate ports for simplicity, but could be done using single port and multiple routes
  user_data                   = <<EOF
#!/bin/bash
sudo apt update
sudo apt install -y nodejs
sudo apt install -y npm
cat << 'EOT' > /home/ubuntu/server.js
    const http = require('http');
            const { exec } = require('child_process');

exec("curl -s http://169.254.169.254/latest/meta-data/instance-id", (error, instanceId) => {
    exec("curl -s http://169.254.169.254/latest/meta-data/public-ipv4", (error, ipAddress) => {
        exec("curl -s http://169.254.169.254/latest/meta-data/mac", (error, macAddress) => {
            http.createServer(function (req, res) {
                res.writeHead(200, { 'Content-Type': 'text/html' });
                res.end(`Instance ID: $${instanceId}<br>IP Address: $${ipAddress}<br>MAC Address: $${macAddress}`);
            }).listen(81);
        });
    });
});

http.createServer(function (req, res) {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end("Health Check OK");
    }).listen(80);
EOT
sudo npm install -g pm2
pm2 start /home/ubuntu/server.js
pm2 startup
pm2 save
EOF
  associate_public_ip_address = true
  security_groups             = [aws_security_group.elb.id]
}

resource "aws_autoscaling_group" "web" {
  name_prefix       = "web-asg-"
  max_size          = 3
  min_size          = 1
  desired_capacity  = 1
  target_group_arns = [aws_lb_target_group.front_end.arn]

  vpc_zone_identifier  = aws_subnet.public.*.id
  launch_configuration = aws_launch_configuration.web.id

  health_check_type         = "ELB"
  health_check_grace_period = 300

  lifecycle {
    create_before_destroy = true
  }
}
