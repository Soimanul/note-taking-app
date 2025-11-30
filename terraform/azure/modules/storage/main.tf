resource "azurerm_storage_account" "main" {
  name                     = "notetakingappstorage"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_share" "media" {
  name                 = "media"
  storage_account_name = azurerm_storage_account.main.name
  quota                = 100  # 100 GB
}

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_account_key" {
  description = "Storage account primary access key"
  value       = azurerm_storage_account.main.primary_access_key
  sensitive   = true
}

output "storage_share_name" {
  description = "Storage share name for media files"
  value       = azurerm_storage_share.media.name
}
