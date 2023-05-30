variable "region" {
  description = "AWS region"
}

variable "access_key" {
  description = "AWS access key"
  sensitive   = true
}

variable "secret_key" {
  description = "AWS secret key"
  sensitive   = true
}

variable "instance_type" {
  description = "Type of instance to start"
}

variable "ami" {
  description = "AMI to use for the instances"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks and AZs for the public subnets"
  type        = list(object({ cidr = string, az = string }))
}
