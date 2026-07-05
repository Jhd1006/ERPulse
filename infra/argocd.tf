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

resource "null_resource" "delete_loadbalancer_svc" {
    triggers = {
      cluster_name = aws_eks_cluster.main.name
      region       = var.aws_region
    }

    provisioner "local-exec" {
      when    = destroy
      command = "aws eks update-kubeconfig --name ${self.triggers.cluster_name} --region ${self.triggers.region} && kubectl delete svc erpulse-api --ignore-not-found=true"
    }

    depends_on = [kubectl_manifest.erpulse_api_app]
  }
