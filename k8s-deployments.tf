resource "kubernetes_secret" "db_creds" {
  metadata {
    name      = "db-creds"
    namespace = "default"
  }

  data = {
    username = var.db_user
    password = var.db_password
  }
}

resource "kubernetes_secret" "backend_app_secret" {
  metadata {
    name      = "backend-app-secret"
    namespace = "default"
  }

  data = {
    session_secret  = var.session_secret
    mailgun_api_key = var.mailgun_api_key
  }
}

resource "kubernetes_deployment" "backend" {
  metadata {
    name   = "backend"
    labels = { app = "backend" }
  }

  spec {
    replicas = 2

    selector {
      match_labels = { app = "backend" }
    }

    template {
      metadata {
        labels = { app = "backend" }
      }

      spec {
        container {
          name  = "backend"
          image = "docker.io/deniziy/backend:latest"

          port { container_port = 5000 }

          #resources {
            #requests = {
              #cpu    = "100m"
              #memory = "128Mi"
            #}
            #limits = {
              #cpu    = "500m"
              #memory = "512Mi"
            #}
          #}

          env {
            name  = "DB_HOST"
            value = google_compute_instance.mysql_vm.network_interface[0].network_ip
          }
          env {
            name  = "DB_NAME"
            value = var.db_name
          }
          env {
            name  = "NODE_ENV"
            value = var.node_env
          }

          env {
            name = "DB_USER"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_creds.metadata[0].name
                key  = "username"
              }
            }
          }
          env {
            name = "DB_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.db_creds.metadata[0].name
                key  = "password"
              }
            }
          }

          env {
            name = "SESSION_SECRET"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.backend_app_secret.metadata[0].name
                key  = "session_secret"
              }
            }
          }
          env {
            name = "MAILGUN_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.backend_app_secret.metadata[0].name
                key  = "mailgun_api_key"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "backend" {
  metadata { name = "backend-service" }

  spec {
    selector = { app = "backend" }

    port {
      port        = 5000
      target_port = 5000
    }

    type = "LoadBalancer"
    session_affinity = "ClientIP"
  }
}

resource "kubernetes_deployment" "frontend" {
  metadata {
    name   = "frontend"
    labels = { app = "frontend" }
  }

  # ensure the Cloud Function exists first
  depends_on = [
    google_cloudfunctions_function.send_newsletter
  ]

  spec {
    replicas = 2

    selector {
      match_labels = { app = "frontend" }
    }

    template {
      metadata {
        labels = { app = "frontend" }
      }

      spec {
        container {
          name  = "frontend"
          image = "docker.io/deniziy/frontend-prod:latest"

          port { container_port = 80 }

          env {
            name  = "CHOKIDAR_USEPOLLING"
            value = "true"
          }
          env {
            name  = "DANGEROUSLY_DISABLE_HOST_CHECK"
            value = tostring(var.dangerously_disable_host_check)
          }
          env {
            name  = "HOST"
            value = "0.0.0.0"
          }
          env {
            name  = "PORT"
            value = "3000"
          }
          env {
            name  = "REACT_APP_NEWSLETTER_FUNCTION_URL"
            value = google_cloudfunctions_function.send_newsletter.https_trigger_url
          }
        }
      }
    }
  }
}


resource "kubernetes_service" "frontend" {
  metadata { name = "frontend-service" }

  spec {
    selector = { app = "frontend" }

    port {
      port        = 3000
      target_port = 80
    }

    type = "LoadBalancer"
  }
}

# Horizontal Pod Autoscaler for Backend
resource "kubernetes_horizontal_pod_autoscaler_v2" "backend_hpa" {
  metadata {
    name = "backend-hpa"
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.backend.metadata[0].name
    }

    min_replicas = 2
    max_replicas = 10

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type               = "Utilization"
          average_utilization = 60
        }
      }
    }
  }
}

# Horizontal Pod Autoscaler for Frontend
resource "kubernetes_horizontal_pod_autoscaler_v2" "frontend_hpa" {
  metadata {
    name = "frontend-hpa"
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.frontend.metadata[0].name
    }

    min_replicas = 2
    max_replicas = 10

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type               = "Utilization"
          average_utilization = 60
        }
      }
    }
  }
}
