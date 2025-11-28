#!/bin/bash
#cloud-config
users:
  - name: ${admin_user}
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups: docker
    shell: /bin/bash
    ssh_authorized_keys:
      - ${ssh_key}

packages:
  - apt-transport-https
  - ca-certificates
  - curl
  - gnupg
  - lsb-release

runcmd:
  - |
    set -euo pipefail
    # Install Docker using official convenience script (works for Ubuntu)
    curl -fsSL https://get.docker.com | sh
    # Install docker compose plugin if available
    apt-get update -y && apt-get install -y docker-compose-plugin || true
    # Ensure docker service is enabled and started
    systemctl enable --now docker || true
    # Create app directory and set ownership
    mkdir -p /opt/app
    chown -R ${admin_user}:${admin_user} /opt/app || true
    # If an SSH key was supplied via template, install it for the admin user
    if [ -n "${ssh_key}" ]; then
      mkdir -p /home/${admin_user}/.ssh
      echo "${ssh_key}" >> /home/${admin_user}/.ssh/authorized_keys
      chown -R ${admin_user}:${admin_user} /home/${admin_user}/.ssh || true
      chmod 700 /home/${admin_user}/.ssh || true
      chmod 600 /home/${admin_user}/.ssh/authorized_keys || true
    fi

final_message: "Cloud-init finished."
