terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }

  backend "s3" {
    bucket = "tfstate-444065722670"
    key    = "reliabilityos/03-ecr/terraform.tfstate"
    region = "us-east-1"
  }
}
