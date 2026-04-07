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

              export DEBIAN_FRONTEND=noninteractive

              apt-get update -y
              apt-get install -y python3 python3-pip python3-venv git

              mkdir -p /apps
              cd /apps

              if [ ! -d BiteCo ]; then
                git clone -b ${var.repository_branch} ${var.repository_url} BiteCo
              fi

              cd /apps/BiteCo
              git fetch origin
              git checkout ${var.repository_branch}
              git pull origin ${var.repository_branch}

              python3 -m venv /apps/BiteCo/venv
              /apps/BiteCo/venv/bin/pip install --upgrade pip
              /apps/BiteCo/venv/bin/pip install -r /apps/BiteCo/requirements.txt

              cat > /etc/biteco.env <<EOF
              DJANGO_SECRET_KEY=biteco-secret-key
              DEBUG=False
              ALLOWED_HOSTS=*
              INSTANCE_NAME=backend-${each.key}
              USE_CACHE=True
              CACHE_BACKEND=local
              EOF

              set -a
              . /etc/biteco.env
              set +a

              cd /apps/BiteCo
              /apps/BiteCo/venv/bin/python manage.py migrate

              cat > /etc/systemd/system/biteco.service <<EOF
              [Unit]
              Description=BiteCo Django Gunicorn
              After=network.target

              [Service]
              User=root
              WorkingDirectory=/apps/BiteCo
              EnvironmentFile=/etc/biteco.env
              ExecStart=/apps/BiteCo/venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000
              Restart=always

              [Install]
              WantedBy=multi-user.target
              EOF

              systemctl daemon-reload
              systemctl enable biteco
              systemctl restart biteco
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

              export DEBIAN_FRONTEND=noninteractive

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

              nginx -t
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
