resource "random_string" "acct_suffix" {
  length  = 6
  upper   = false
  special = false
}
variable "existing_storage_account_name" {
  description = "If set, use an existing storage account for tfstate instead of creating one. Leave empty to create a new account."
  type        = string
  default     = "noteapptfstateqafaup"
}

variable "storage_account_prefix" {
  description = "Prefix for the terraform state storage account when creating a new one"
  type        = string
  default     = "noteapptfstate"
}

# If the user provided an existing storage account name, use the data source.
data "azurerm_storage_account" "existing" {
  count               = var.existing_storage_account_name == "" ? 0 : 1
  name                = var.existing_storage_account_name
  resource_group_name = var.resource_group_name
}

# Create a new storage account only when no existing name was provided.
resource "azurerm_storage_account" "tfstate" {
  count                    = var.existing_storage_account_name == "" ? 1 : 0
  name                     = lower("${var.storage_account_prefix}${random_string.acct_suffix.result}")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "tfstate" {
  name                  = "tfstate"
  storage_account_id    = var.existing_storage_account_name != "" ? data.azurerm_storage_account.existing[0].id : azurerm_storage_account.tfstate[0].id
  container_access_type = "private"
}

output "tfstate_storage_account_name" {
  value = var.existing_storage_account_name != "" ? var.existing_storage_account_name : azurerm_storage_account.tfstate[0].name
}

output "tfstate_container_name" {
  value = azurerm_storage_container.tfstate.name
}
