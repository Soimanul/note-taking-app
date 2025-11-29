variable "resource_group_name" {
  description = "Resource group name where ACR exists"
  type        = string
}

variable "acr_login_server" {
  description = "ACR login server (e.g., myacr.azurecr.io)"
  type        = string
}

variable "principal_id" {
  description = "Principal ID of the managed identity to grant ACR pull access"
  type        = string
}