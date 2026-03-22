resource "aws_iam_role" "loki" {
  count = var.enable_loki ? 1 : 0
  name  = "${var.cluster_name}-loki-irsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = aws_iam_openid_connect_provider.kubernetes.arn
      }
      Condition = {
        StringEquals = {
          "${local.oidc_url}:aud" = "sts.amazonaws.com"
          "${local.oidc_url}:sub" = "system:serviceaccount:logging:loki"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_policy" "loki" {
  count       = var.enable_loki ? 1 : 0
  name        = "${var.cluster_name}-AllowLokiS3Access"
  description = "IAM policy for Loki S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.loki_s3_bucket}",
          "arn:aws:s3:::${var.loki_s3_bucket}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "loki" {
  count      = var.enable_loki ? 1 : 0
  policy_arn = aws_iam_policy.loki[0].arn
  role       = aws_iam_role.loki[0].name
}
