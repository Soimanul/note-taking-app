// Get the existing ACR resource
data "azurerm_container_registry" "existing" {
  name                = split(".", var.acr_login_server)[0]
  resource_group_name = var.resource_group_name
}

// Grant AcrPull role to the managed identity
resource "azurerm_role_assignment" "acr_pull" {
  scope                = data.azurerm_container_registry.existing.id
  role_definition_name = "AcrPull"
  principal_id         = var.principal_id
}