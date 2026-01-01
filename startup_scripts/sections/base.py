"""Base system setup: updates, Docker, Flox, and system dependencies."""

import json

from constants import DOCKER_CONFIG, FLOX_VERSION


def get_system_updates() -> str:
    """Generate system updates section."""
    return '''
section_start "System Updates"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
section_end "System Updates"
'''


def get_docker_install() -> str:
    """Generate Docker installation section."""
    docker_config_json = json.dumps(DOCKER_CONFIG, indent=4)
    return f'''
section_start "Docker Install"
apt-get install -y \\
    apt-transport-https \\
    ca-certificates \\
    curl \\
    gnupg \\
    lsb-release \\
    software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Configure Docker for better performance
cat > /etc/docker/daemon.json << 'DOCKEREOF'
{docker_config_json}
DOCKEREOF

systemctl restart docker
section_end "Docker Install"
'''


def get_flox_install() -> str:
    """Generate Flox installation section."""
    return f'''
section_start "Flox Install"

# Install Flox via .deb package - see https://flox.dev/docs/install-flox/install/
wget -q "https://downloads.flox.dev/by-env/stable/deb/flox-{FLOX_VERSION}.x86_64-linux.deb" -O /tmp/flox.deb
dpkg -i /tmp/flox.deb
rm /tmp/flox.deb

echo "Flox installed:"
flox --version

# Configure Flox to disable direnv prompts (enables headless/non-interactive activation)
mkdir -p /home/ph/.config/flox
cat > /home/ph/.config/flox/flox.toml << 'FLOXCONFIGEOF'
[features]
direnv = false
FLOXCONFIGEOF
chown -R ph:ph /home/ph/.config
section_end "Flox Install"
'''


def get_system_deps() -> str:
    """Generate system dependencies installation section."""
    return '''
section_start "System Dependencies"

# Build essentials and common tools (Flox handles dev tools)
apt-get install -y \\
    build-essential \\
    git \\
    curl \\
    wget \\
    vim \\
    htop \\
    jq \\
    unzip \\
    screen
section_end "System Dependencies"
'''


def get_user_creation() -> str:
    """Generate user creation section."""
    return '''
section_start "User Creation"
if ! id ph &>/dev/null; then
    useradd -m -s /bin/bash ph
fi
usermod -aG docker,sudo ph
section_end "User Creation"
'''
