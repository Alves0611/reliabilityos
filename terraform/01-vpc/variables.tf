variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
  default     = "studying-vpc"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr_block, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "public_subnets" {
  description = "List of public subnets"
  type = list(object({
    cidr_block        = string
    availability_zone = string
    name              = string
  }))
  default = [
    {
      cidr_block        = "10.0.1.0/24"
      availability_zone = "us-east-1a"
      name              = "studying-public-1a"
    },
    {
      cidr_block        = "10.0.2.0/24"
      availability_zone = "us-east-1b"
      name              = "studying-public-1b"
    }
  ]
}

variable "private_subnets" {
  description = "List of private subnets"
  type = list(object({
    cidr_block        = string
    availability_zone = string
    name              = string
  }))
  default = [
    {
      cidr_block        = "10.0.10.0/24"
      availability_zone = "us-east-1a"
      name              = "studying-private-1a"
    },
    {
      cidr_block        = "10.0.11.0/24"
      availability_zone = "us-east-1b"
      name              = "studying-private-1b"
    }
  ]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_s3_endpoint" {
  description = "Enable S3 VPC Gateway endpoint"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
