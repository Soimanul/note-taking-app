// Root module wiring: reference modules and wire images + create Postgres/Redis

locals {
  app_suffix = "-notetakingapp"
  location   = "westeurope"
}

// Identities module: create shared user-assigned identity for the three apps
module "identities" {
  source              = "./modules/identities"
  resource_group_name = var.resource_group_name
  location            = local.location
}

// Role assignment module: grant AcrPull to the shared identity on existing ACR
module "assign_acr_pull" {
  source              = "./modules/role_assignments"
  resource_group_name = var.resource_group_name
  acr_login_server    = var.acr_login_server
  principal_id        = module.identities.identity_principal_id
}

// Container Apps environment
module "containerapps_env" {
  source              = "./modules/containerapps_env"
  resource_group_name = var.resource_group_name
  location            = local.location
}

// Postgres (managed) - create if requested
module "postgres" {
  source              = "./modules/postgres"
  resource_group_name = var.resource_group_name
  location            = local.location
  create              = var.create_postgres
}

// Redis (managed)
module "redis" {
  source              = "./modules/redis"
  resource_group_name = var.resource_group_name
  location            = local.location
  create              = var.create_redis
}

// Container Apps: backend (Django web server)
module "backend_app" {
  source              = "./modules/containerapp"
  name                = "backend${local.app_suffix}"
  resource_group_name = var.resource_group_name
  location            = local.location
  environment_id      = module.containerapps_env.containerapps_env_id
  image               = var.backend_image
  identity_id         = module.identities.identity_id
  ingress_enabled     = true
  target_port         = 8000
  command             = []  // Uses Dockerfile's default CMD (gunicorn)
  min_replicas        = 1
  cpu                 = 2.0
  memory              = "4Gi"

  env_vars = {
    DEBUG                  = "False"
    DJANGO_SETTINGS_MODULE = "config.settings"
    ALLOWED_HOSTS          = "*"
    # CORS_ALLOWED_ORIGINS uses wildcard default in settings.py
  }
  
  secrets = {
    SECRET_KEY       = var.django_secret_key
    GOOGLE_API_KEY   = var.google_api_key
    PINECONE_API_KEY = var.pinecone_api_key
    POSTGRES_HOST    = module.postgres.postgres_host
    POSTGRES_PORT    = "5432"
    POSTGRES_DB      = module.postgres.postgres_database
    POSTGRES_USER    = module.postgres.postgres_user
    POSTGRES_PASSWORD = module.postgres.postgres_password
    REDIS_URL        = module.redis.redis_url
  }

  depends_on = [
    module.assign_acr_pull,
    module.postgres,
    module.redis
  ]
}

// Container Apps: worker (Celery worker using same backend image)
module "worker_app" {
  source              = "./modules/containerapp"
  name                = "worker${local.app_suffix}"
  resource_group_name = var.resource_group_name
  location            = local.location
  environment_id      = module.containerapps_env.containerapps_env_id
  image               = var.backend_image  // Same image as backend!
  identity_id         = module.identities.identity_id
  ingress_enabled     = false  // Worker doesn't need HTTP ingress
  command             = ["celery", "-A", "config", "worker", "-l", "info", "--concurrency=2"]
  min_replicas        = 1
  cpu                 = 2.0
  memory              = "4Gi"

  env_vars = {
    DEBUG                  = "False"
    DJANGO_SETTINGS_MODULE = "config.settings"
  }
  
  secrets = {
    SECRET_KEY        = var.django_secret_key
    GOOGLE_API_KEY    = var.google_api_key
    PINECONE_API_KEY  = var.pinecone_api_key
    POSTGRES_HOST     = module.postgres.postgres_host
    POSTGRES_PORT     = "5432"
    POSTGRES_DB       = module.postgres.postgres_database
    POSTGRES_USER     = module.postgres.postgres_user
    POSTGRES_PASSWORD = module.postgres.postgres_password
    REDIS_URL         = module.redis.redis_url
  }

  depends_on = [
    module.assign_acr_pull,
    module.postgres,
    module.redis
  ]
}

// Container Apps: frontend
module "frontend_app" {
  source              = "./modules/containerapp"
  name                = "frontend${local.app_suffix}"
  resource_group_name = var.resource_group_name
  location            = local.location
  environment_id      = module.containerapps_env.containerapps_env_id
  image               = var.frontend_image
  identity_id         = module.identities.identity_id
  ingress_enabled     = true
  target_port         = 80
  command             = []  // Uses Dockerfile's default CMD
  
  env_vars = {
    REACT_APP_API_URL = module.backend_app.url
  }
  
  secrets = {}

  depends_on = [
    module.assign_acr_pull,
    module.backend_app
  ]
}