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

resource "helm_release" "argocd_apps" {
  name       = "argocd-apps"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argocd-apps"
  version    = "2.0.6"
  namespace  = kubernetes_namespace.argocd.metadata[0].name

  values = [yamlencode({
    applications = {
      erpulse-api = {
        namespace = "argocd"
        project   = "default"
        source = {
          repoURL        = "https://github.com/Jhd1006/ERPulse"
          targetRevision = "main"
          path           = "manifest"
        }
        destination = {
          server    = "https://kubernetes.default.svc"
          namespace = "default"
        }
        syncPolicy = {
          automated = { prune = true, selfHeal = true }
          retry = {
            limit   = 5
            backoff = { duration = "30s", factor = 2, maxDuration = "5m" }
          }
        }
        ignoreDifferences = [{
          group        = "apps"
          kind         = "Deployment"
          jsonPointers = ["/spec/replicas"]
        }]
      }
    }
  })]

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

    depends_on = [helm_release.argocd_apps]
  }

