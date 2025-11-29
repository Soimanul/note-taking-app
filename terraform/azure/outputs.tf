output "frontend_url" {
  description = "Frontend Container App URL"
  value       = module.frontend_app.url
}

output "backend_url" {
  description = "Backend Container App URL"
  value       = module.backend_app.url
}

output "backend_name" {
  description = "Backend Container App name"
  value       = module.backend_app.name
}

output "worker_name" {
  description = "Worker Container App name"
  value       = module.worker_app.name
}

output "postgres_host" {
  description = "Postgres server hostname"
  value       = module.postgres.postgres_host
  sensitive   = true
}

output "redis_hostname" {
  description = "Redis hostname"
  value       = module.redis.redis_hostname
  sensitive   = true
}