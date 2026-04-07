terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_prefix" {
  description = "Prefix used for naming AWS resources"
  type        = string
  default     = "biteco"
}

variable "instance_type" {
  description = "EC2 instance type for hosts"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "Existing AWS key pair name for SSH access"
  type        = string
}

variable "repository_url" {
  description = "Git repository URL for the BiteCo project"
  type        = string
  default     = "https://github.com/JulianRestrespo/BiteCo.git"
}

variable "repository_branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}

provider "aws" {
  region = var.region
}

locals {
  project_name = "${var.project_prefix}-cloud-cost-platform"

  common_tags = {
    Project   = local.project_name
    ManagedBy = "Terraform"
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "traffic_ssh" {
  name        = "${var.project_prefix}-traffic-ssh"
  description = "Allow SSH access"

  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-ssh"
  })
}

resource "aws_security_group" "traffic_backend" {
  name        = "${var.project_prefix}-traffic-backend"
  description = "Allow backend traffic on port 8000"

  ingress {
    description = "Django/Gunicorn app"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-backend"
  })
}

resource "aws_security_group" "traffic_lb" {
  name        = "${var.project_prefix}-traffic-lb"
  description = "Allow load balancer traffic on port 80"

  ingress {
    description = "HTTP access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-traffic-lb"
  })
}

resource "aws_instance" "backend" {
  for_each = toset(["a", "b", "c"])

  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids = [
    aws_security_group.traffic_backend.id,
    aws_security_group.traffic_ssh.id
  ]

  user_data = <<-EOT
              #!/bin/bash
              set -e

              apt-get update -y
              apt-get install -y python3-pip python3-venv git

              mkdir -p /apps
              cd /apps

              if [ ! -d BiteCo ]; then
                git clone ${var.repository_url} BiteCo
              fi

              cd BiteCo
              git fetch origin
              git checkout ${var.repository_branch}
              git pull origin ${var.repository_branch}

              python3 -m venv venv
              . venv/bin/activate
              pip install --upgrade pip
              pip install -r requirements.txt

              echo 'DJANGO_SECRET_KEY="biteco-secret-key"' >> /etc/environment
              echo 'DEBUG="False"' >> /etc/environment
              echo 'ALLOWED_HOSTS="*"' >> /etc/environment
              echo 'INSTANCE_NAME="backend-${each.key}"' >> /etc/environment
              echo 'USE_CACHE="True"' >> /etc/environment
              echo 'CACHE_BACKEND="local"' >> /etc/environment

              set -a
              . /etc/environment
              set +a

              cd /apps/BiteCo
              python manage.py migrate

              nohup /apps/BiteCo/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000 > /var/log/biteco.log 2>&1 &
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-backend-${each.key}"
    Role = "backend"
  })
}

resource "aws_instance" "load_balancer" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  associate_public_ip_address = true
  vpc_security_group_ids = [
    aws_security_group.traffic_lb.id,
    aws_security_group.traffic_ssh.id
  ]

  user_data = <<-EOT
              #!/bin/bash
              set -e

              apt-get update -y
              apt-get install -y nginx

              cat > /etc/nginx/sites-available/default <<'NGINXCONF'
              upstream biteco_backends {
                  server ${aws_instance.backend["a"].private_ip}:8000;
                  server ${aws_instance.backend["b"].private_ip}:8000;
                  server ${aws_instance.backend["c"].private_ip}:8000;
              }

              server {
                  listen 80 default_server;
                  listen [::]:80 default_server;

                  location / {
                      proxy_pass http://biteco_backends;
                      proxy_set_header Host $host;
                      proxy_set_header X-Real-IP $remote_addr;
                      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                      proxy_set_header X-Forwarded-Proto $scheme;
                  }
              }
              NGINXCONF

              systemctl restart nginx
              systemctl enable nginx
              EOT

  tags = merge(local.common_tags, {
    Name = "${var.project_prefix}-lb"
    Role = "load-balancer"
  })

  depends_on = [aws_instance.backend]
}

output "load_balancer_public_ip" {
  description = "Public IP of the load balancer"
  value       = aws_instance.load_balancer.public_ip
}

output "backend_public_ips" {
  description = "Public IPs of backend instances"
  value       = { for id, instance in aws_instance.backend : id => instance.public_ip }
}

output "backend_private_ips" {
  description = "Private IPs of backend instances"
  value       = { for id, instance in aws_instance.backend : id => instance.private_ip }
}