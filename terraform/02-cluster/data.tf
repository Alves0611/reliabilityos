data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "tfstate-444065722670"
    key    = "reliabilityos/01-vpc/terraform.tfstate"
    region = "us-east-1"
  }
}
