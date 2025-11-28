output "vm_name" {
  value       = azurerm_linux_virtual_machine.vm.name
  description = "Name of the Linux VM used for deploying containers"
}

output "resource_group_name" {
  value       = data.azurerm_resource_group.rg.name
  description = "Resource group containing the VM"
}

output "public_ip" {
  value       = azurerm_public_ip.pip.ip_address
  description = "Public IP address assigned to the VM"
}

