resource "azurerm_user_assigned_identity" "container_apps" {
  name                = "notetakingapp-identity"
  resource_group_name = var.resource_group_name
  location            = var.location
}

output "identity_id" {
  description = "Full resource ID of the managed identity"
  value       = azurerm_user_assigned_identity.container_apps.id
}

output "identity_principal_id" {
  description = "Principal ID (object ID) for role assignments"
  value       = azurerm_user_assigned_identity.container_apps.principal_id
}

output "identity_client_id" {
  description = "Client ID of the managed identity"
  value       = azurerm_user_assigned_identity.container_apps.client_id
}