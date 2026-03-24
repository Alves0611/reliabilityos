resource "helm_release" "argocd" {
  count            = var.enable_argocd ? 1 : 0
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "7.8.13"
  namespace        = "argocd"
  create_namespace = true

  cleanup_on_fail = true
  wait            = true
  timeout         = 600

  depends_on = [
    aws_eks_node_group.this,
    aws_eks_access_policy_association.admin,
  ]
}

resource "kubernetes_secret_v1" "argocd_repo_creds" {
  count = var.enable_argocd ? 1 : 0

  metadata {
    name      = "github-repo-creds"
    namespace = "argocd"
    labels = {
      "argocd.argoproj.io/secret-type" = "repo-creds"
    }
  }

  data = {
    type     = "git"
    url      = "https://github.com/Alves0611"
    username = "argocd"
    password = var.github_token
  }

  depends_on = [helm_release.argocd]
}

resource "kubectl_manifest" "app_of_apps" {
  count = var.enable_argocd ? 1 : 0

  yaml_body = <<-YAML
    apiVersion: argoproj.io/v1alpha1
    kind: Application
    metadata:
      name: app-of-apps
      namespace: argocd
      finalizers:
        - resources-finalizer.argocd.argoproj.io
    spec:
      project: default
      source:
        repoURL: https://github.com/Alves0611/reliabilityos.git
        targetRevision: main
        path: argocd
      destination:
        server: https://kubernetes.default.svc
        namespace: argocd
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
  YAML

  depends_on = [helm_release.argocd]
}
