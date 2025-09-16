#!/bin/bash
#
# This script prepares a fresh Ubuntu server for running the Warenwelt project.
# It includes creating a new user, setting up the UFW firewall,
# hardening SSH, and installing Docker, Docker Compose, and fail2ban.

set -e
set -o pipefail
set -u
set -x

# --- Script Functions ---

# Function to print messages
print_message() {
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
}

# Function to handle errors
handle_error() {
    echo "Error on line $1"
    exit 1
}

# Trap errors
trap 'handle_error $LINENO' ERR

# --- Main Script ---

# Check if the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Please use sudo."
    exit 1
fi

print_message "Starting Ubuntu Server Setup for Warenwelt"

# Step 1: Update and Upgrade System
print_message "Updating and upgrading the system..."
apt-get update
apt-get upgrade -y
apt-get dist-upgrade -y
apt-get autoremove -y
apt-get autoclean -y

# Step 2: Create a new user with sudo privileges
print_message "Creating a new user..."
read -p "Enter the username for the new user: " NEW_USER
if id "$NEW_USER" &>/dev/null; then
    echo "User '$NEW_USER' already exists. Skipping user creation."
else
    adduser --gecos "" "$NEW_USER"
    usermod -aG sudo "$NEW_USER"
    # Copy authorized_keys for SSH access
    if [ -d "/root/.ssh" ]; then
        mkdir -p "/home/$NEW_USER/.ssh"
        cp /root/.ssh/authorized_keys "/home/$NEW_USER/.ssh/authorized_keys"
        chown -R "$NEW_USER":"$NEW_USER" "/home/$NEW_USER/.ssh"
        chmod 700 "/home/$NEW_USER/.ssh"
        chmod 600 "/home/$NEW_USER/.ssh/authorized_keys"
        echo "SSH keys for root have been copied to the new user."
    else
        echo "No SSH keys found for root. Please add an SSH key for the new user manually."
    fi
    echo "User '$NEW_USER' created and added to the sudo group."
fi

# Step 3: Configure UFW (Uncomplicated Firewall)
print_message "Configuring the firewall (UFW)..."
apt-get install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw --force enable
ufw status verbose

# Step 4: Harden SSH
print_message "Hardening SSH configuration..."
SSH_CONFIG_FILE="/etc/ssh/sshd_config"
# Disable root login
sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' "$SSH_CONFIG_FILE"
sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin no/' "$SSH_CONFIG_FILE"
# Disable password authentication
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' "$SSH_CONFIG_FILE"
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' "$SSH_CONFIG_FILE"
# Restart SSH service to apply changes
systemctl restart sshd
echo "SSH has been hardened."

# Step 5: Install Docker and Docker Compose
print_message "Installing Docker and Docker Compose..."
# Install prerequisites
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
LATEST_COMPOSE=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
DOCKER_COMPOSE_URL="https://github.com/docker/compose/releases/download/${LATEST_COMPOSE}/docker-compose-$(uname -s)-$(uname -m)"
curl -L "$DOCKER_COMPOSE_URL" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
echo "Docker and Docker Compose installed successfully."

# Step 6: Add the new user to the docker group
print_message "Adding user '$NEW_USER' to the docker group..."
usermod -aG docker "$NEW_USER"
echo "User '$NEW_USER' has been added to the docker group. They will need to log out and log back in for the changes to take effect."

# Step 7: Install fail2ban
print_message "Installing fail2ban..."
apt-get install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
echo "fail2ban has been installed and started."

print_message "Setup complete! Please review the output above."
print_message "IMPORTANT: If you are logged in as root, please log out and log in as the new user '$NEW_USER'."
print_message "The new user will need to log out and log back in to use Docker without sudo."
