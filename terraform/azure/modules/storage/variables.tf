variable "create" {
  description = "Whether to create the storage account"
  type        = bool
  default     = true
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}
