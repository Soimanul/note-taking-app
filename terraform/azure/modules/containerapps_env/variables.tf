variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "storage_account_name" {
  description = "Storage account name for Azure Files"
  type        = string
  default     = null
}

variable "storage_account_key" {
  description = "Storage account key for Azure Files"
  type        = string
  default     = null
  sensitive   = true
}

variable "storage_share_name" {
  description = "Storage share name for media files"
  type        = string
  default     = null
}