resource "azurerm_log_analytics_workspace" "main" {
  name                = "notetakingapp-logs"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "main" {
  name                       = "notetakingapp-env"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

output "containerapps_env_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.main.id
}

output "containerapps_env_default_domain" {
  description = "Default domain for Container Apps"
  value       = azurerm_container_app_environment.main.default_domain
}