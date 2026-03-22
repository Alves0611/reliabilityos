aws_region       = "us-east-1"
cluster_name     = "studying-cluster"
cluster_version  = "1.34"

node_group_capacity_type  = "ON_DEMAND"
node_group_instance_types = ["t3.medium"]
node_group_desired_size   = 2
node_group_min_size       = 2
node_group_max_size       = 2

admin_principal_arn = "arn:aws:iam::444065722670:role/github-actions-terraform"
enable_ebs_csi_driver = true
enable_external_dns   = true
enable_nginx_ingress  = true
enable_loki           = true
loki_s3_bucket        = "loki-logs-444065722670"
enable_argocd         = true
