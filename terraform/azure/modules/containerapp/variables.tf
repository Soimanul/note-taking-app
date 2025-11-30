variable "name" {
  description = "Container App name"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "environment_id" {
  description = "Container Apps Environment ID"
  type        = string
}

variable "image" {
  description = "Container image (e.g., myacr.azurecr.io/app:tag)"
  type        = string
}

variable "identity_id" {
  description = "Managed identity ID for ACR pull"
  type        = string
}

variable "ingress_enabled" {
  description = "Whether to enable HTTP ingress"
  type        = bool
  default     = false
}

variable "external_ingress" {
  description = "Whether ingress is external (public)"
  type        = bool
  default     = true
}

variable "target_port" {
  description = "Container port to expose"
  type        = number
  default     = 8000
}

variable "command" {
  description = "Container startup command override"
  type        = list(string)
  default     = []
}

variable "env_vars" {
  description = "Environment variables (non-secret)"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "Secret environment variables"
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "min_replicas" {
  description = "Minimum number of replicas"
  type        = number
  default     = 0
}

variable "max_replicas" {
  description = "Maximum number of replicas"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU allocation (e.g., 0.25, 0.5, 1.0)"
  type        = number
  default     = 0.25
}

variable "memory" {
  description = "Memory allocation (e.g., 0.5Gi, 1Gi)"
  type        = string
  default     = "0.5Gi"
}

variable "tcp_scale_rule" {
  description = "TCP scale rule configuration"
  type = object({
    name                = string
    concurrent_requests = number
  })
  default = null
}

variable "volume_mounts" {
  description = "Volume mount configurations"
  type = list(object({
    name              = string
    storage_type      = string
    storage_name      = string
    mount_path        = string
    access_mode       = string
  }))
  default = []
}