resource "random_password" "postgres" {
  count   = var.create ? 1 : 0
  length  = 24
  special = true
}

resource "azurerm_postgresql_flexible_server" "main" {
  count               = var.create ? 1 : 0
  name                = "notetakingapp-postgres"
  resource_group_name = var.resource_group_name
  location            = var.location
  
  administrator_login    = "noteappuser"
  administrator_password = random_password.postgres[0].result
  
  sku_name   = "B_Standard_B1ms"
  storage_mb = 32768
  version    = "15"
  
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  
  public_network_access_enabled = true
  
  zone = "1"
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  count     = var.create ? 1 : 0
  name      = "noteappdb"
  server_id = azurerm_postgresql_flexible_server.main[0].id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  count            = var.create ? 1 : 0
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.main[0].id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

output "postgres_host" {
  description = "PostgreSQL server hostname"
  value       = var.create ? azurerm_postgresql_flexible_server.main[0].fqdn : ""
}

output "postgres_user" {
  description = "PostgreSQL admin username"
  value       = var.create ? azurerm_postgresql_flexible_server.main[0].administrator_login : ""
}

output "postgres_password" {
  description = "PostgreSQL admin password"
  value       = var.create ? random_password.postgres[0].result : ""
  sensitive   = true
}

output "postgres_database" {
  description = "PostgreSQL database name"
  value       = var.create ? azurerm_postgresql_flexible_server_database.main[0].name : ""
}