variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "create" {
  description = "Whether to create the Redis cache"
  type        = bool
  default     = true
}