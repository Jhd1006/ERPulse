resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }

  depends_on = [aws_eks_node_group.main]
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = "7.7.11"
  namespace  = kubernetes_namespace.argocd.metadata[0].name

  depends_on = [aws_eks_node_group.main]
}

resource "kubectl_manifest" "erpulse_api_app" {
  yaml_body = <<-YAML
    apiVersion: argoproj.io/v1alpha1
    kind: Application
    metadata:
      name: erpulse-api
      namespace: argocd
    spec:
      project: default
      source:
        repoURL: https://github.com/Jhd1006/ERPulse
        targetRevision: main
        path: manifest
      destination:
        server: https://kubernetes.default.svc
        namespace: default
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
  YAML

  depends_on = [helm_release.argocd]
}
