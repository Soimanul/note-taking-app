terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    # Backend config is provided via CLI flags in GitHub Actions
    # -backend-config="resource_group_name=..."
    # -backend-config="storage_account_name=..."
    # -backend-config="container_name=..."
    # -backend-config="key=..."
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}