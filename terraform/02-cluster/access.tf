resource "aws_eks_access_entry" "admin" {
  count = var.admin_principal_arn != "" ? 1 : 0

  cluster_name  = aws_eks_cluster.this.name
  principal_arn = var.admin_principal_arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "admin" {
  count = var.admin_principal_arn != "" ? 1 : 0

  cluster_name  = aws_eks_cluster.this.name
  principal_arn = aws_eks_access_entry.admin[0].principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}
