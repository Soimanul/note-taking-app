variable "resource_group_name" {
  description = "Resource group to deploy into"
  type        = string
  default     = "BCSAI2025-DEVOPS-STUDENTS-A"
}

variable "acr_login_server" {
  description = "Existing ACR login server (e.g. myacr.azurecr.io)"
  type        = string
  default     = "notetakingappregistry.azurecr.io"
}

variable "backend_image" {
  description = "Backend image URI (used for both web and worker)"
  type        = string
}

variable "frontend_image" {
  description = "Frontend image URI"
  type        = string
}

variable "create_postgres" {
  description = "Whether to create PostgreSQL server"
  type        = bool
  default     = true
}

variable "create_redis" {
  description = "Whether to create Redis cache"
  type        = bool
  default     = true
}

variable "django_secret_key" {
  description = "Django SECRET_KEY (injected via TF_VAR_django_secret_key)"
  type        = string
  sensitive   = true
}

variable "google_api_key" {
  description = "Google API Key"
  type        = string
  sensitive   = true
}

variable "pinecone_api_key" {
  description = "Pinecone API Key"
  type        = string
  sensitive   = true
}