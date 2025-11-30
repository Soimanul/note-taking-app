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

resource "azurerm_container_app_environment_storage" "media" {
  count                            = var.storage_account_name != null ? 1 : 0
  name                             = "media-files"
  container_app_environment_id     = azurerm_container_app_environment.main.id
  account_name                     = var.storage_account_name
  access_key                       = var.storage_account_key
  share_name                       = var.storage_share_name
  access_mode                      = "ReadWrite"
}

output "containerapps_env_id" {
  description = "Container Apps Environment ID"
  value       = azurerm_container_app_environment.main.id
}

output "containerapps_env_default_domain" {
  description = "Default domain for Container Apps"
  value       = azurerm_container_app_environment.main.default_domain
}