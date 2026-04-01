variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "studying-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.34"
}

variable "authentication_mode" {
  description = "Authentication mode for the EKS cluster"
  type        = string
  default     = "API_AND_CONFIG_MAP"
}

variable "node_group_name" {
  description = "Name of the EKS node group"
  type        = string
  default     = ""
}

variable "node_group_capacity_type" {
  description = "Capacity type for the node group (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_group_capacity_type)
    error_message = "Must be ON_DEMAND or SPOT."
  }
}

variable "node_group_instance_types" {
  description = "List of EC2 instance types for the node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_group_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_group_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 2
}

variable "node_group_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 2
}

variable "admin_principal_arn" {
  description = "ARN of the IAM user/role to grant admin access to the cluster"
  type        = string
  default     = ""
}

variable "enable_ebs_csi_driver" {
  description = "Enable EBS CSI driver addon"
  type        = bool
  default     = true
}

variable "enable_external_dns" {
  description = "Deploy External DNS with IRSA"
  type        = bool
  default     = true
}

variable "enable_nginx_ingress" {
  description = "Deploy NGINX Ingress Controller"
  type        = bool
  default     = true
}

variable "enable_loki" {
  description = "Create Loki IRSA role for S3 access"
  type        = bool
  default     = true
}

variable "loki_s3_bucket" {
  description = "S3 bucket name for Loki log storage"
  type        = string
  default     = ""
}

variable "enable_tempo" {
  description = "Create Tempo IRSA role and S3 bucket for trace storage"
  type        = bool
  default     = true
}

variable "tempo_s3_bucket" {
  description = "S3 bucket name for Tempo trace storage"
  type        = string
  default     = "tempo-traces-444065722670"
}

variable "enable_argocd" {
  description = "Deploy ArgoCD with app-of-apps pattern"
  type        = bool
  default     = true
}

variable "github_token" {
  description = "GitHub PAT for ArgoCD to access private repositories"
  type        = string
  default     = ""
  sensitive   = true
}

variable "custom_domain" {
  description = "Base domain for all services"
  type        = string
  default     = "gabrielstudying.click"
}

variable "hosted_zone_name" {
  description = "Route53 hosted zone name"
  type        = string
  default     = "gabrielstudying.click"
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
