"""Generate complete startup script for PostHog development VMs."""

import json

from config import ClaudeCodeConfig, CodexCliConfig, MonitoringConfig, RemoteDesktopConfig, RepoConfig
from constants import (
    DEFAULT_MPROCS_CONFIG,
    DOCKER_CONFIG,
    FLOX_VERSION,
    POSTHOG_ENV_DEFAULTS,
    SYSCTL_SETTINGS,
)


def generate_startup_script(
    posthog_branch: str = "master",
    additional_repos: list[RepoConfig] | None = None,
    enable_minimal_mode: bool = False,
    monitoring: MonitoringConfig | None = None,
    claude_code: ClaudeCodeConfig | None = None,
    remote_desktop: RemoteDesktopConfig | None = None,
    codex_cli: CodexCliConfig | None = None,
) -> str:
    """Generate a complete startup script for PostHog development.

    The script uses Flox (PostHog's recommended approach) which manages:
    - Python (via uv)
    - Node.js 22
    - mprocs
    - Rust toolchain
    - All other development dependencies

    Steps:
    1. Updates system packages
    2. Installs monitoring agents (GCP Ops Agent, Netdata)
    3. Installs Docker and Docker Compose
    4. Installs Flox
    5. Clones PostHog and optional additional repositories
    6. Activates Flox environment (installs all deps via on-activate hook)
    7. Installs Claude Code (optional)
    8. Installs Remote Desktop - XFCE + xrdp + Chrome (optional)
    9. Installs OpenAI Codex CLI (optional)

    Args:
        posthog_branch: Git branch for PostHog repo
        additional_repos: List of additional repos to clone
        enable_minimal_mode: Whether to configure for minimal mode
        monitoring: Monitoring agents configuration
        claude_code: Claude Code installation configuration
        remote_desktop: Remote desktop (xrdp) configuration
        codex_cli: OpenAI Codex CLI installation configuration

    Returns:
        Complete bash startup script as string
    """
    additional_repos = additional_repos or []
    monitoring = monitoring or MonitoringConfig()
    claude_code = claude_code or ClaudeCodeConfig()
    remote_desktop = remote_desktop or RemoteDesktopConfig()
    codex_cli = codex_cli or CodexCliConfig()

    # Build GCP Ops Agent installation
    ops_agent_install = ""
    if monitoring.ops_agent_enabled:
        ops_agent_install = '''
# ========================================
# 2a. Install GCP Ops Agent
# ========================================
echo ">>> Installing GCP Ops Agent"
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install
rm add-google-cloud-ops-agent-repo.sh
systemctl enable google-cloud-ops-agent
echo ">>> GCP Ops Agent installed"
'''

    # Build Netdata installation
    netdata_install = ""
    if monitoring.netdata_enabled and monitoring.netdata_claim_token:
        netdata_install = f'''
# ========================================
# 2b. Install Netdata
# ========================================
echo ">>> Installing Netdata"
wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh
sh /tmp/netdata-kickstart.sh --stable-channel --non-interactive \\
    --claim-token {monitoring.netdata_claim_token} \\
    --claim-rooms {monitoring.netdata_claim_rooms} \\
    --claim-url {monitoring.netdata_claim_url}
rm /tmp/netdata-kickstart.sh
echo ">>> Netdata installed and claimed"
'''

    # Build Claude Code installation (binary only - user config happens after user creation)
    claude_code_binary_install = ""
    claude_code_user_config = ""
    if claude_code.enabled and claude_code.api_key:
        claude_code_binary_install = '''
# ========================================
# 2c. Install Claude Code (binary)
# ========================================
echo ">>> Installing Claude Code binary"
curl -fsSL https://claude.ai/install.sh | bash
echo ">>> Claude Code binary installed (user config will be done after user creation)"
'''
        claude_code_user_config = f'''
# ========================================
# 3b. Configure Claude Code for ph user
# ========================================
echo ">>> Configuring Claude Code for ph user"

# Create Claude Code configuration directory for ph user
mkdir -p /home/ph/.claude

# Create settings.json with API key and permissions for headless use
cat > /home/ph/.claude/settings.json << 'CLAUDEEOF'
{{
  "permissions": {{
    "allow": ["Bash", "Read", "Edit", "Write", "Glob", "Grep", "WebFetch"]
  }}
}}
CLAUDEEOF

# Set environment variable for API key in user's profile
cat >> /home/ph/.bashrc << 'CLAUDEENVEOF'

# Claude Code configuration
export ANTHROPIC_API_KEY="{claude_code.api_key}"
export PATH="$HOME/.local/bin:$PATH"
alias claude='~/.local/bin/claude'
CLAUDEENVEOF

chown -R ph:ph /home/ph/.claude
echo ">>> Claude Code configured for ph user"
'''

    # Build Remote Desktop (xrdp + XFCE + Chrome) installation
    # Split into package install (before user creation) and user config (after user creation)
    remote_desktop_install = ""
    remote_desktop_user_config = ""
    if remote_desktop.enabled and remote_desktop.password:
        remote_desktop_install = '''
# ========================================
# 2d. Install Remote Desktop (xrdp + XFCE + Chrome)
# ========================================
echo ">>> Installing XFCE desktop environment"
DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    xfce4 xfce4-goodies \\
    dbus-x11 \\
    xorg

echo ">>> Installing xrdp (RDP server)"
apt-get install -y xrdp

# Add xrdp user to ssl-cert group (required for TLS)
usermod -aG ssl-cert xrdp

echo ">>> Installing Chrome browser"
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

echo ">>> Installing Chrome Remote Desktop"
wget -q https://dl.google.com/linux/direct/chrome-remote-desktop_current_amd64.deb -O /tmp/crd.deb
apt-get install -y /tmp/crd.deb || apt-get install -y -f
rm /tmp/crd.deb

# Enable and start xrdp (user config happens after user creation)
systemctl enable xrdp
systemctl start xrdp

echo ">>> Remote Desktop packages installed (user config will be done after user creation)"
'''
        remote_desktop_user_config = f'''
# ========================================
# 3c. Configure Remote Desktop for ph user
# ========================================
echo ">>> Configuring Remote Desktop for ph user"

# Add ph to chrome-remote-desktop group (if it exists)
if getent group chrome-remote-desktop > /dev/null 2>&1; then
    usermod -aG chrome-remote-desktop ph
    echo ">>> Added ph to chrome-remote-desktop group"
else
    echo ">>> Warning: chrome-remote-desktop group not found, creating it"
    groupadd chrome-remote-desktop
    usermod -aG chrome-remote-desktop ph
fi

# Configure Chrome Remote Desktop to use XFCE
echo "exec /usr/bin/xfce4-session" > /home/ph/.chrome-remote-desktop-session
chmod +x /home/ph/.chrome-remote-desktop-session
chown ph:ph /home/ph/.chrome-remote-desktop-session

# Configure XFCE as the session for xrdp
echo "xfce4-session" > /home/ph/.xsession
chown ph:ph /home/ph/.xsession

# Set password for ph user (for RDP login)
echo "ph:{remote_desktop.password}" | chpasswd

echo ">>> Remote Desktop configured - connect via RDP to port 3389"
echo ">>> Username: ph"
'''

    # Build Codex CLI installation (user config - needs npm from Flox)
    codex_cli_user_config = ""
    if codex_cli.enabled and codex_cli.api_key:
        codex_cli_user_config = f'''
# ========================================
# 3d. Configure OpenAI Codex CLI for ph user
# ========================================
echo ">>> Installing OpenAI Codex CLI for ph user"

# Install Codex CLI globally using npm (available via Flox)
su - ph -c "cd /home/ph/posthog && FLOX_NO_DIRENV_SETUP=1 flox activate -- npm install -g @openai/codex" || true

# Set environment variable for API key in user's profile
cat >> /home/ph/.bashrc << 'CODEXENVEOF'

# OpenAI Codex CLI configuration
export OPENAI_API_KEY="{codex_cli.api_key}"
CODEXENVEOF

echo ">>> Codex CLI installed for ph user"
'''

    # Build the additional repos clone commands
    additional_clone_commands = ""
    for repo in additional_repos:
        additional_clone_commands += f'''
echo ">>> Cloning {repo.url} (branch: {repo.branch})"
git clone --branch {repo.branch} {repo.url} /home/ph/{repo.target_dir}
chown -R ph:ph /home/ph/{repo.target_dir}
'''

    minimal_env = 'export POSTHOG_MINIMAL_MODE="true"' if enable_minimal_mode else ""
    # Use hogli start (Flox-managed) with appropriate flags
    # Default to mprocs-with-logging.yaml for file-based logging (useful for code agents)
    start_cmd = "hogli start --minimal" if enable_minimal_mode else f"hogli start --custom {DEFAULT_MPROCS_CONFIG}"

    # Generate Docker config JSON
    docker_config_json = json.dumps(DOCKER_CONFIG, indent=4)

    # Generate sysctl settings
    sysctl_lines = "\n".join(f"{k}={v}" for k, v in SYSCTL_SETTINGS.items())

    # Generate .env file content
    env_lines = "\n".join(f"{k}={v}" for k, v in POSTHOG_ENV_DEFAULTS.items())
    if minimal_env:
        env_lines += "\nPOSTHOG_MINIMAL_MODE=true"

    script = f'''#!/bin/bash
#
# PostHog Development VM Startup Script
# Generated by posthog-dev-pulumi
#
# Uses Flox for dependency management (PostHog's recommended approach)
# See: https://posthog.com/handbook/engineering/developing-locally#setup-with-flox-recommended
#
set -ex

LOG_FILE="/var/log/posthog-startup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "PostHog Dev VM Startup - $(date)"
echo "========================================"

# ========================================
# 1. System Updates
# ========================================
echo ">>> Updating system packages"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

{ops_agent_install}
{netdata_install}
{claude_code_binary_install}
{remote_desktop_install}
# ========================================
# 2. Install Docker
# ========================================
echo ">>> Installing Docker"
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

# ========================================
# 3. Create Development User
# ========================================
echo ">>> Creating ph user"
if ! id ph &>/dev/null; then
    useradd -m -s /bin/bash ph
fi
usermod -aG docker ph

{claude_code_user_config}
{remote_desktop_user_config}
# ========================================
# 4. Install System Dependencies
# ========================================
echo ">>> Installing system dependencies"

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

# ========================================
# 5. Install Flox
# ========================================
echo ">>> Installing Flox (PostHog's recommended dev environment manager)"

# Install Flox via .deb package - see https://flox.dev/docs/install-flox/install/
wget -q "https://downloads.flox.dev/by-env/stable/deb/flox-{FLOX_VERSION}.x86_64-linux.deb" -O /tmp/flox.deb
dpkg -i /tmp/flox.deb
rm /tmp/flox.deb

echo ">>> Flox installed"
flox --version

# Configure Flox to disable direnv prompts (enables headless/non-interactive activation)
echo ">>> Configuring Flox for headless operation"
mkdir -p /home/ph/.config/flox
cat > /home/ph/.config/flox/flox.toml << 'FLOXCONFIGEOF'
[features]
direnv = false
FLOXCONFIGEOF
chown -R ph:ph /home/ph/.config

# ========================================
# 6. Clone Repositories
# ========================================
echo ">>> Cloning PostHog repository (branch: {posthog_branch})"

# Check if branch exists remotely
if git ls-remote --heads https://github.com/posthog/posthog.git {posthog_branch} | grep -q {posthog_branch}; then
    echo ">>> Branch '{posthog_branch}' exists, cloning directly"
    git clone --branch {posthog_branch} https://github.com/posthog/posthog.git /home/ph/posthog
else
    echo ">>> Branch '{posthog_branch}' does not exist, cloning master and creating new branch"
    git clone https://github.com/posthog/posthog.git /home/ph/posthog
    cd /home/ph/posthog
    git checkout -b {posthog_branch}
    cd /
fi

chown -R ph:ph /home/ph/posthog

{additional_clone_commands}

# ========================================
# 7. Setup PostHog Environment
# ========================================
echo ">>> Setting up PostHog environment"

# Create environment file
cat > /home/ph/posthog/.env << 'ENVEOF'
{env_lines}
ENVEOF

chown ph:ph /home/ph/posthog/.env

# Create simple PostHog start script (localhost access via Remote Desktop)
cat > /home/ph/start-posthog.sh << 'STARTSCRIPTEOF'
#!/bin/bash
# Simple PostHog start script (localhost access via RDP)
# Generated by posthog-dev-pulumi startup script
cd /home/ph/posthog
FLOX_NO_DIRENV_SETUP=1 exec flox activate -- mprocs --config bin/mprocs-with-logging.yaml
STARTSCRIPTEOF

chmod +x /home/ph/start-posthog.sh
chown ph:ph /home/ph/start-posthog.sh
echo ">>> Created /home/ph/start-posthog.sh"

# ========================================
# 8. Configure /etc/hosts for PostHog services
# ========================================
echo ">>> Configuring /etc/hosts for PostHog services"
# Add required entries to /etc/hosts if not present (needed for Docker service resolution)
if ! grep -q "kafka clickhouse clickhouse-coordinator objectstorage" /etc/hosts; then
    echo "127.0.0.1 kafka clickhouse clickhouse-coordinator objectstorage" >> /etc/hosts
    echo ">>> /etc/hosts amended for PostHog services"
else
    echo ">>> /etc/hosts already contains required entries"
fi

# ========================================
# 8a. Activate Flox Environment
# ========================================
echo ">>> Activating Flox environment (this installs all dependencies)"
echo ">>> This may take several minutes on first run..."

# Run flox activate in non-interactive mode to install all dependencies
# The on-activate hook in .flox/env/manifest.toml handles:
# - Python environment setup (uv sync)
# - Node.js dependencies (pnpm install)
# Note: /etc/hosts already configured above (Flox can't sudo in non-interactive mode)
# FLOX_NO_DIRENV_SETUP=1 prevents interactive direnv setup prompt
su - ph -c "cd /home/ph/posthog && FLOX_NO_DIRENV_SETUP=1 flox activate -- echo 'Flox environment activated'" || true

# Download GeoLite2 database
echo ">>> Downloading GeoLite2 database"
su - ph -c "cd /home/ph/posthog && FLOX_NO_DIRENV_SETUP=1 flox activate -- ./bin/download-mmdb" || true

{codex_cli_user_config}
# ========================================
# 8b. Start Docker Services & Run Migrations
# ========================================
echo ">>> Starting Docker services"
# Use || true to continue even if some containers fail (e.g., port conflicts with otel-collector)
su - ph -c "cd /home/ph/posthog && docker compose -f docker-compose.dev.yml up -d" || true

echo ">>> Waiting for Docker services to be ready..."
sleep 30

# Ensure critical services are running (db, redis, clickhouse, kafka)
echo ">>> Verifying critical services..."
su - ph -c "cd /home/ph/posthog && docker compose -f docker-compose.dev.yml ps db redis clickhouse kafka"

echo ">>> Running database migrations"
su - ph -c "cd /home/ph/posthog && FLOX_NO_DIRENV_SETUP=1 flox activate -- bin/migrate" || true

# ========================================
# 8c. Create Makefile for Common Commands
# ========================================
echo ">>> Creating Makefile"

cat > /home/ph/posthog/Makefile.dev << 'MAKEFILEEOF'
# PostHog Development VM - Handy Commands
# Usage: make -f Makefile.dev <target>

.PHONY: start start-minimal attach logs ps down migrate demo-data restart clean help

# Start PostHog (with logging)
start:
	FLOX_NO_DIRENV_SETUP=1 flox activate -- hogli start --custom bin/mprocs-with-logging.yaml

# Start PostHog in minimal mode
start-minimal:
	FLOX_NO_DIRENV_SETUP=1 flox activate -- hogli start --minimal

# Attach to running PostHog screen session
attach:
	screen -r posthog

# View Docker logs
logs:
	docker compose -f docker-compose.dev.yml logs -f

# Show Docker container status
ps:
	docker compose -f docker-compose.dev.yml ps

# Stop Docker containers
down:
	docker compose -f docker-compose.dev.yml down

# Run database migrations
migrate:
	FLOX_NO_DIRENV_SETUP=1 flox activate -- bin/migrate

# Generate demo data
demo-data:
	FLOX_NO_DIRENV_SETUP=1 flox activate -- python manage.py generate_demo_data

# Restart Docker services
restart:
	docker compose -f docker-compose.dev.yml down
	docker compose -f docker-compose.dev.yml up -d

# Clean up everything (Docker volumes, caches)
clean:
	docker compose -f docker-compose.dev.yml down -v
	rm -rf node_modules .venv

# Tail PostHog log files
tail:
	tail -f /tmp/posthog-*.log

# Show help
help:
	@echo "PostHog Development VM Commands"
	@echo ""
	@echo "  make -f Makefile.dev start        - Start PostHog (with logging)"
	@echo "  make -f Makefile.dev start-minimal - Start PostHog (minimal mode)"
	@echo "  make -f Makefile.dev attach       - Attach to running screen session"
	@echo "  make -f Makefile.dev logs         - View Docker logs"
	@echo "  make -f Makefile.dev ps           - Show Docker status"
	@echo "  make -f Makefile.dev down         - Stop Docker containers"
	@echo "  make -f Makefile.dev migrate      - Run database migrations"
	@echo "  make -f Makefile.dev demo-data    - Generate demo data"
	@echo "  make -f Makefile.dev restart      - Restart Docker services"
	@echo "  make -f Makefile.dev clean        - Clean up everything"
	@echo "  make -f Makefile.dev tail         - Tail log files"
	@echo ""
MAKEFILEEOF

chown ph:ph /home/ph/posthog/Makefile.dev

# ========================================
# 8d. Start PostHog in Screen Session
# ========================================
echo ">>> Starting PostHog in background screen session"

# Wait a bit for migrations to settle
sleep 10

# Start PostHog in a detached screen session using the start script
# The start script:
# - Sets JS_URL/JS_POSTHOG_UI_HOST to external IP for browser access
# - Sources the Python venv (flox profile scripts only run for interactive shells)
# - Runs mprocs via flox activate
su - ph -c "screen -dmS posthog /home/ph/start-posthog.sh"

echo ">>> PostHog started in screen session 'posthog'"
echo ">>> Attach with: screen -r posthog"

# ========================================
# 9. Setup Shell Environment
# ========================================
echo ">>> Configuring shell environment"

cat >> /home/ph/.bashrc << 'BASHRCEOF'

# PostHog Development Environment (Flox-based)
export POSTHOG_DIR="$HOME/posthog"

# Auto-activate Flox when entering PostHog directory
cd() {{
    builtin cd "$@"
    if [[ "$PWD" == "$POSTHOG_DIR"* ]] && [[ -d "$POSTHOG_DIR/.flox" ]]; then
        if [[ -z "$FLOX_ENV" ]]; then
            echo "Activating Flox environment..."
            eval "$(FLOX_NO_DIRENV_SETUP=1 flox activate)"
        fi
    fi
}}

# Convenience aliases
alias ph='cd $POSTHOG_DIR'
alias phattach='screen -r posthog'
alias phstart='cd $POSTHOG_DIR && FLOX_NO_DIRENV_SETUP=1 flox activate -- hogli start --custom bin/mprocs-with-logging.yaml'
alias phminimal='cd $POSTHOG_DIR && FLOX_NO_DIRENV_SETUP=1 flox activate -- hogli start --minimal'
alias phlogs='docker compose -f $POSTHOG_DIR/docker-compose.dev.yml logs -f'
alias phps='docker compose -f $POSTHOG_DIR/docker-compose.dev.yml ps'
alias phdown='docker compose -f $POSTHOG_DIR/docker-compose.dev.yml down'
alias phtail='tail -f /tmp/posthog-*.log'
alias phmake='make -f $POSTHOG_DIR/Makefile.dev'
alias floxsh='cd $POSTHOG_DIR && FLOX_NO_DIRENV_SETUP=1 flox activate'

echo ""
echo "========================================"
echo "PostHog Development VM Ready! (Flox)"
echo "========================================"
echo ""
echo "PostHog is running in a screen session!"
echo ""
echo "Quick commands:"
echo "  phattach    - Attach to running PostHog (screen session)"
echo "  phtail      - Tail all PostHog log files"
echo "  phlogs      - View Docker container logs"
echo "  phps        - Show Docker container status"
echo "  phdown      - Stop Docker containers"
echo "  phmake help - Show all make commands"
echo ""
echo "To attach to mprocs:"
echo "  phattach"
echo "  (Ctrl+A, D to detach without stopping)"
echo ""
echo "In mprocs, press 'r' on generate-demo-data to create test data."
echo ""
echo "PostHog directory: $POSTHOG_DIR"
echo ""
BASHRCEOF

chown ph:ph /home/ph/.bashrc

# ========================================
# 10. Final Setup
# ========================================
echo ">>> Running final setup"

# Increase system limits for Docker/ClickHouse
cat >> /etc/sysctl.conf << 'SYSCTLEOF'
# Docker/ClickHouse optimizations
{sysctl_lines}
SYSCTLEOF
sysctl -p

# Pre-pull Docker images to speed up first start
echo ">>> Pre-pulling Docker images (this may take a while)"
su - ph -c "cd /home/ph/posthog && docker compose -f docker-compose.dev-minimal.yml pull" || true

echo "========================================"
echo "PostHog Dev VM Startup Complete - $(date)"
echo "========================================"
echo ""
echo "PostHog is running in a screen session!"
echo ""
echo "ACCESS OPTIONS:"
echo ""
echo "  Chrome Remote Desktop (one-time setup required):"
echo "    1. SSH to VM: gcloud compute ssh <vm-name> --zone=europe-west1-b"
echo "    2. Switch user: sudo su - ph"
echo "    3. Go to: https://remotedesktop.google.com/headless"
echo "    4. Click 'Begin' > 'Next' > 'Authorize'"
echo "    5. Copy the Debian Linux command and run it on the VM"
echo "    6. Set a PIN when prompted"
echo "    7. Then connect via: https://remotedesktop.google.com/access"
echo ""
echo "  xrdp (alternative - no setup needed):"
echo "    Connect to <external-ip>:3389 with any RDP client"
echo "    Username: ph"
echo ""
echo "  SSH:"
echo "    gcloud compute ssh <vm-name> --zone=europe-west1-b"
echo "    sudo su - ph"
echo "    phattach  (attach to mprocs)"
echo ""
echo "Detach from screen: Ctrl+A, D"
echo "In mprocs, press 'r' on generate-demo-data to create test data."
echo ""
echo "Makefile commands: phmake help"
echo ""
'''

    return script
