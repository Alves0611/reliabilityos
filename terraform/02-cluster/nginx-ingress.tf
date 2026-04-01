resource "helm_release" "nginx_ingress" {
  count            = var.enable_nginx_ingress ? 1 : 0
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.12.1"
  namespace        = "ingress-nginx"
  create_namespace = true

  cleanup_on_fail = true
  wait            = true
  timeout         = 600

  values = [yamlencode({
    controller = {
      service = {
        type = "LoadBalancer"
        annotations = {
          "service.beta.kubernetes.io/aws-load-balancer-type"              = "external"
          "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type"   = "ip"
          "service.beta.kubernetes.io/aws-load-balancer-scheme"            = "internet-facing"
          "service.beta.kubernetes.io/aws-load-balancer-ssl-cert"          = aws_acm_certificate_validation.this.certificate_arn
          "service.beta.kubernetes.io/aws-load-balancer-ssl-ports"         = "443"
          "service.beta.kubernetes.io/aws-load-balancer-backend-protocol"  = "tcp"
        }
        targetPorts = {
          https = "http"
        }
      }
    }
  })]

  depends_on = [
    aws_eks_node_group.this,
    aws_eks_access_policy_association.admin,
    aws_acm_certificate_validation.this,
    helm_release.load_balancer_controller,
  ]
}
