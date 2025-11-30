resource "azurerm_storage_account" "main" {
  count                    = var.create ? 1 : 0
  name                     = "notetakingappstorage"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Enable blob public access for media files
  allow_nested_items_to_be_public = false
}

resource "azurerm_storage_container" "media" {
  count                 = var.create ? 1 : 0
  name                  = "media"
  storage_account_name  = azurerm_storage_account.main[0].name
  container_access_type = "private"
}

output "account_name" {
  description = "Storage account name"
  value       = var.create ? azurerm_storage_account.main[0].name : ""
}

output "account_key" {
  description = "Storage account primary access key"
  value       = var.create ? azurerm_storage_account.main[0].primary_access_key : ""
  sensitive   = true
}

output "container_name" {
  description = "Storage container name for media files"
  value       = var.create ? azurerm_storage_container.media[0].name : ""
}
