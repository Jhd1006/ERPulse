resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
  }

  depends_on = [aws_eks_node_group.main]
}

resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "65.5.1"

  values = [
    yamlencode({
      alertmanager = {
        config = {
          route = {
            receiver        = "slack-notifications"
            group_by        = ["alertname"]
            group_wait      = "30s"
            group_interval  = "5m"
            repeat_interval = "3h"
          }
          receivers = [
            {
              name = "null"
            },
            {
              name = "slack-notifications"
              slack_configs = [
                {
                  send_resolved = true
                  title         = "{{ .CommonAnnotations.summary }}"
                  text          = "{{ .CommonAnnotations.description }}"
                }
              ]
            }
          ]
        }
      }
    })
  ]

  set_sensitive {
    name  = "alertmanager.config.global.slack_api_url"
    value = var.slack_webhook_url
  }

  depends_on = [aws_eks_node_group.main]
}