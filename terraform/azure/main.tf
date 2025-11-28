data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

# VM extension to perform GHCR login (using protected settings) and deploy the compose stack
resource "azurerm_virtual_machine_extension" "ghcr_deploy" {
  name                 = "${var.vm_name}-ghcr-deploy"
  virtual_machine_id   = azurerm_linux_virtual_machine.vm.id
  publisher            = "Microsoft.Azure.Extensions"
  type                 = "CustomScript"
  type_handler_version = "2.1"

  settings = <<SETTINGS
{
  "commandToExecute": "bash /var/lib/waagent/custom-script/download/0/deploy.sh"
}
SETTINGS

  protected_settings = <<PROTECTED
{
  "script": "#!/usr/bin/env bash\nset -euo pipefail\n\nGHCR_USER=\"${var.ghcr_user}\"\nGHCR_PAT=\"${var.ghcr_pat}\"\nIMAGE=\"${var.image}\"\n\n# Ensure docker is available (cloud-init should have installed it)\nif ! command -v docker >/dev/null 2>&1; then echo 'docker not found' >&2; exit 1; fi\n\n# Login to GHCR and pull/start the image\necho \"Logging into ghcr.io as ${var.ghcr_user}\"\necho \"${var.ghcr_pat}\" | docker login ghcr.io -u \"${var.ghcr_user}\" --password-stdin || true\n\nmkdir -p /opt/app\ncat > /opt/app/docker-compose.yml <<'EOL'\nversion: '3.8'\nservices:\n  app:\n    image: ${var.image}\n    restart: always\n    ports:\n      - \"80:8000\"\nEOL\n\n# Pull and start the compose stack\ndocker compose -f /opt/app/docker-compose.yml pull || true\ndocker compose -f /opt/app/docker-compose.yml up -d || docker-compose -f /opt/app/docker-compose.yml up -d || true\n"
}
PROTECTED
}

resource "azurerm_virtual_network" "vnet" {
  name                = "${var.vm_name}-vnet"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = var.location
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "subnet" {
  name                 = "${var.vm_name}-subnet"
  resource_group_name  = data.azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_network_security_group" "nsg" {
  name                = "${var.vm_name}-nsg"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = var.location

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "assoc" {
  subnet_id                 = azurerm_subnet.subnet.id
  network_security_group_id = azurerm_network_security_group.nsg.id
}

resource "azurerm_public_ip" "pip" {
  name                = "${var.vm_name}-pip"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = var.location
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_interface" "nic" {
  name                = "${var.vm_name}-nic"
  location            = var.location
  resource_group_name = data.azurerm_resource_group.rg.name

  ip_configuration {
    name                          = "ipconfig"
    subnet_id                     = azurerm_subnet.subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip.id
  }
}

resource "azurerm_linux_virtual_machine" "vm" {
  name                  = var.vm_name
  resource_group_name   = data.azurerm_resource_group.rg.name
  location              = var.location
  size                  = var.vm_size
  admin_username        = var.admin_username
  network_interface_ids = [azurerm_network_interface.nic.id]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts-gen2"
    version   = "latest"
  }

  identity {
    type = "SystemAssigned"
  }

  dynamic "admin_ssh_key" {
    for_each = var.admin_ssh_public_key == "" ? [] : [var.admin_ssh_public_key]
    content {
      username   = var.admin_username
      public_key = admin_ssh_key.value
    }
  }

  # Enforce SSH-only access: password authentication disabled.
  disable_password_authentication = true

  custom_data = base64encode(templatefile("${path.module}/cloud-init.tpl", {
    admin_user = var.admin_username
    ssh_key    = var.admin_ssh_public_key
  }))
}

# VM extension to perform GHCR login (using protected settings) and deploy backend+frontend
resource "azurerm_virtual_machine_extension" "ghcr_deploy" {
  name                 = "${var.vm_name}-ghcr-deploy"
  virtual_machine_id   = azurerm_linux_virtual_machine.vm.id
  publisher            = "Microsoft.Azure.Extensions"
  type                 = "CustomScript"
  type_handler_version = "2.1"

  settings = <<SETTINGS
{
  "commandToExecute": "bash /var/lib/waagent/custom-script/download/0/deploy.sh"
}
SETTINGS

  protected_settings = <<PROTECTED
{
  "script": "#!/usr/bin/env bash\nset -euo pipefail\n\nGHCR_USER=\"${var.ghcr_user}\"\nGHCR_PAT=\"${var.ghcr_pat}\"\nBACKEND_IMAGE=\"${var.backend_image}\"\nFRONTEND_IMAGE=\"${var.frontend_image}\"\n\n# ensure docker exists (cloud-init installs it)\nif ! command -v docker >/dev/null 2>&1; then echo 'docker not found' >&2; exit 1; fi\n\n# Login to GHCR if credentials provided\necho \"Performing docker login to ghcr.io\"\necho \"${var.ghcr_pat}\" | docker login ghcr.io -u \"${var.ghcr_user}\" --password-stdin || true\n\nmkdir -p /opt/app\ncat > /opt/app/docker-compose.yml <<'EOL'\nversion: '3.8'\nservices:\n  backend:\n    image: ${var.backend_image}\n    restart: unless-stopped\n    ports:\n      - \"8000:8000\"\n  frontend:\n    image: ${var.frontend_image}\n    restart: unless-stopped\n    ports:\n      - \"80:80\"\nEOL\n\n# Pull and start available services (ignore empty image values)\nif [ -n \"${var.backend_image}\" ] || [ -n \"${var.frontend_image}\" ]; then\n  docker compose -f /opt/app/docker-compose.yml pull || true\n  docker compose -f /opt/app/docker-compose.yml up -d --remove-orphans || docker-compose -f /opt/app/docker-compose.yml up -d --remove-orphans || true\nfi\n"
}
PROTECTED
}
