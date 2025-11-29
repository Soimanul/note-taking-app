resource "azurerm_container_app" "main" {
  name                         = var.name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = var.environment_id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [var.identity_id]
  }

  registry {
    server   = split("/", var.image)[0]
    identity = var.identity_id
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name    = var.name
      image   = var.image
      cpu     = var.cpu
      memory  = var.memory
      command = length(var.command) > 0 ? var.command : null

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secrets
        content {
          name        = env.key
          secret_name = replace(lower(env.key), "_", "-")
        }
      }

      dynamic "startup_probe" {
        for_each = var.startup_probe != null ? [var.startup_probe] : []
        content {
          transport = startup_probe.value.transport
          port      = startup_probe.value.port
          path      = lookup(startup_probe.value, "path", null)
        }
      }

      dynamic "liveness_probe" {
        for_each = var.liveness_probe != null ? [var.liveness_probe] : []
        content {
          transport = liveness_probe.value.transport
          port      = liveness_probe.value.port
          path      = lookup(liveness_probe.value, "path", null)
        }
      }
    }

    dynamic "tcp_scale_rule" {
      for_each = var.tcp_scale_rule != null ? [var.tcp_scale_rule] : []
      content {
        name                = tcp_scale_rule.value.name
        concurrent_requests = tcp_scale_rule.value.concurrent_requests
      }
    }
  }

  dynamic "ingress" {
    for_each = var.ingress_enabled ? [1] : []
    content {
      external_enabled = var.external_ingress
      target_port      = var.target_port
      transport        = "http"

      traffic_weight {
        latest_revision = true
        percentage      = 100
      }
    }
  }

  dynamic "secret" {
    for_each = var.secrets
    content {
      name  = replace(lower(secret.key), "_", "-")
      value = secret.value
    }
  }
}

output "name" {
  description = "Container App name"
  value       = azurerm_container_app.main.name
}

output "url" {
  description = "Container App URL (if ingress enabled)"
  value       = var.ingress_enabled ? "https://${azurerm_container_app.main.ingress[0].fqdn}" : ""
}

output "fqdn" {
  description = "Container App FQDN"
  value       = var.ingress_enabled ? azurerm_container_app.main.ingress[0].fqdn : ""
}