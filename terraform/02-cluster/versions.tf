terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    tls = {
      source = "hashicorp/tls"
    }
    helm = {
      source = "hashicorp/helm"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
    kubectl = {
      source = "gavinbunney/kubectl"
    }
  }

  backend "s3" {
    bucket = "tfstate-444065722670"
    key    = "reliabilityos/02-cluster/terraform.tfstate"
    region = "us-east-1"
  }
}
