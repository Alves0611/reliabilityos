resource "aws_s3_bucket" "tempo" {
  count  = var.enable_tempo ? 1 : 0
  bucket = var.tempo_s3_bucket

  tags = var.tags
}

resource "aws_s3_bucket_versioning" "tempo" {
  count  = var.enable_tempo ? 1 : 0
  bucket = aws_s3_bucket.tempo[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tempo" {
  count  = var.enable_tempo ? 1 : 0
  bucket = aws_s3_bucket.tempo[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tempo" {
  count  = var.enable_tempo ? 1 : 0
  bucket = aws_s3_bucket.tempo[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "tempo" {
  count  = var.enable_tempo ? 1 : 0
  bucket = aws_s3_bucket.tempo[0].id

  rule {
    id     = "expire-old-traces"
    status = "Enabled"

    expiration {
      days = 14
    }
  }
}

resource "aws_iam_role" "tempo" {
  count = var.enable_tempo ? 1 : 0
  name  = "EKS_Tempo_Role"

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
          "${local.oidc_url}:sub" = "system:serviceaccount:tracing:tempo"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_policy" "tempo" {
  count       = var.enable_tempo ? 1 : 0
  name        = "${var.cluster_name}-AllowTempoS3Access"
  description = "IAM policy for Tempo S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "arn:aws:s3:::${var.tempo_s3_bucket}",
          "arn:aws:s3:::${var.tempo_s3_bucket}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "tempo" {
  count      = var.enable_tempo ? 1 : 0
  policy_arn = aws_iam_policy.tempo[0].arn
  role       = aws_iam_role.tempo[0].name
}
