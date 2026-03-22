locals {
  oidc_url           = replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")
  private_subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnet_ids
}
