resource "azurerm_redis_cache" "main" {
  count               = var.create ? 1 : 0
  name                = "notetakingapp-redis"
  resource_group_name = var.resource_group_name
  location            = var.location
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  
  public_network_access_enabled = true
  
  redis_configuration {
    enable_authentication = true
  }
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = var.create ? azurerm_redis_cache.main[0].hostname : ""
}

output "redis_port" {
  description = "Redis SSL port"
  value       = var.create ? azurerm_redis_cache.main[0].ssl_port : 0
}

output "redis_primary_key" {
  description = "Redis primary access key"
  value       = var.create ? azurerm_redis_cache.main[0].primary_access_key : ""
  sensitive   = true
}

output "redis_url" {
  description = "Redis connection URL"
  value       = var.create ? "rediss://:${azurerm_redis_cache.main[0].primary_access_key}@${azurerm_redis_cache.main[0].hostname}:${azurerm_redis_cache.main[0].ssl_port}/0" : ""
  sensitive   = true
}