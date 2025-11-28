variable "resource_group_name" {
  description = "Name of the existing Azure resource group to use"
  type        = string
  default     = "BCSAI2025-DEVOPS-STUDENTS-A"
}

variable "location" {
  description = "Azure region to deploy into"
  type        = string
  default     = "westeurope"
}

variable "vm_name" {
  description = "Name for the Linux VM"
  type        = string
  default     = "note-taking-app-vm"
}

variable "vm_size" {
  description = "Size of the VM"
  type        = string
  default     = "Standard_B2s"
}

variable "admin_username" {
  description = "Admin username for the VM"
  type        = string
  default     = "azureuser"
}

variable "admin_ssh_public_key" {
  description = "Optional SSH public key for the admin user (leave empty to rely on cloud-init key install)"
  type        = string
  default     = ""
}

variable "image" {
  description = "Container image to deploy on the VM (e.g. ghcr.io/org/repo:tag). Leave empty to skip deploying a compose stack."
  type        = string
  default     = ""
}

variable "backend_image" {
  description = "Container image for the backend (e.g. ghcr.io/org/note-taking-app-backend:tag). Leave empty to skip deploying backend."
  type        = string
  default     = ""
}

variable "frontend_image" {
  description = "Container image for the frontend (e.g. ghcr.io/org/note-taking-app-frontend:tag). Leave empty to skip deploying frontend."
  type        = string
  default     = ""
}

variable "ghcr_user" {
  description = "GHCR username (organization or user) used for docker login when pulling private images"
  type        = string

  validation {
    condition     = (var.backend_image == "" && var.frontend_image == "") || length(trimspace(var.ghcr_user)) > 0
    error_message = "ghcr_user must be provided (and non-empty) when backend_image or frontend_image is set."
  }
}

variable "ghcr_pat" {
  description = "GHCR Personal Access Token used to authenticate to ghcr.io (passed as sensitive protected_setting)"
  type        = string
  sensitive   = true

  validation {
    condition     = (var.backend_image == "" && var.frontend_image == "") || length(trimspace(var.ghcr_pat)) > 0
    error_message = "ghcr_pat must be provided (and non-empty) when backend_image or frontend_image is set."
  }
}