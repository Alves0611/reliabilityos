aws_region     = "us-east-1"
vpc_name       = "studying-vpc"
vpc_cidr_block = "10.0.0.0/16"

public_subnets = [
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

private_subnets = [
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

enable_nat_gateway = true
enable_s3_endpoint = true
