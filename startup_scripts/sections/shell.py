"""Shell configuration: Makefile, bashrc, sysctl, and final message."""

from constants import SYSCTL_SETTINGS


def get_makefile() -> str:
    """Generate Makefile creation section."""
    return '''
section_start "Makefile"

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
	screen -r ph

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
section_end "Makefile"
'''


def get_bashrc() -> str:
    """Generate bashrc configuration section."""
    return '''
section_start "Bashrc"

cat >> /home/ph/.bashrc << 'BASHRCEOF'

# PostHog Development Environment (Flox-based)
export POSTHOG_DIR="$HOME/posthog"
export PATH="$HOME/.local/bin:$PATH"

# Load user secrets if present (keys for optional tooling)
if [[ -f "$HOME/.config/posthog/secrets.env" ]]; then
    set -a
    source "$HOME/.config/posthog/secrets.env"
    set +a
fi

# Auto-activate Flox when entering PostHog directory
cd() {
    builtin cd "$@"
    if [[ "$PWD" == "$POSTHOG_DIR"* ]] && [[ -d "$POSTHOG_DIR/.flox" ]]; then
        if [[ -z "$FLOX_ENV" ]]; then
            echo "Activating Flox environment..."
            eval "$(FLOX_NO_DIRENV_SETUP=1 flox activate)"
        fi
    fi
}

# Convenience aliases
alias ph='cd $POSTHOG_DIR'
alias phattach='screen -r ph'
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

# Ensure login shells also load secrets
cat >> /home/ph/.profile << 'PROFILEEOF'

# Load user secrets if present (keys for optional tooling)
if [[ -f "$HOME/.config/posthog/secrets.env" ]]; then
    set -a
    . "$HOME/.config/posthog/secrets.env"
    set +a
fi
PROFILEEOF

chown ph:ph /home/ph/.bashrc
section_end "Bashrc"
'''


def get_sysctl_and_docker_pull() -> str:
    """Generate sysctl configuration and Docker image pre-pull section."""
    sysctl_lines = "\n".join(f"{k}={v}" for k, v in SYSCTL_SETTINGS.items())

    return f'''
section_start "Sysctl and Docker Pull"

# Increase system limits for Docker/ClickHouse
cat >> /etc/sysctl.conf << 'SYSCTLEOF'
# Docker/ClickHouse optimizations
{sysctl_lines}
SYSCTLEOF
sysctl -p

# Pre-pull Docker images to speed up first start
if [ "$SKIP_HEAVY" = "1" ]; then
    echo "Skipping Docker pull (base image detected)"
    section_end "Sysctl and Docker Pull"
else
    echo "Pre-pulling Docker images (this may take a while)..."
    su - ph -c "cd /home/ph/posthog && docker compose -f docker-compose.dev-minimal.yml pull" || true
    section_end "Sysctl and Docker Pull"
fi
'''


def get_final_message() -> str:
    """Generate final completion message."""
    return '''
TOTAL_TIME=$(($(date +%s) - SCRIPT_START_TIME))
echo ""
echo "========================================"
echo "PostHog Dev VM Startup Complete - $(date)"
echo "Total time: ${TOTAL_TIME}s ($(($TOTAL_TIME / 60))m $(($TOTAL_TIME % 60))s)"
echo "========================================"
echo ""
echo "TIMING SUMMARY (see /var/log/posthog-startup-timing.log for CSV):"
echo "----------------------------------------"
cat "$TIMING_FILE" | column -t -s,
echo "----------------------------------------"
echo ""
echo "Docker services are running. PostHog dev server ready to start."
echo ""
echo "ACCESS OPTIONS:"
echo ""
echo "  Chrome Remote Desktop (one-time setup required):"
echo "    1. SSH to VM: gcloud compute ssh <vm-name> --tunnel-through-iap"
echo "    2. Switch user: sudo su - ph"
echo "    3. Go to: https://remotedesktop.google.com/headless"
echo "    4. Click 'Begin' > 'Next' > 'Authorize'"
echo "    5. Copy the Debian Linux command and run it on the VM"
echo "    6. Set a PIN when prompted"
echo "    7. Then connect via: https://remotedesktop.google.com/access"
echo ""
echo "  SSH (via IAP tunnel - no external IP needed):"
echo "    gcloud compute ssh <vm-name> --tunnel-through-iap"
echo "    sudo su - ph"
echo ""
echo "TO START POSTHOG DEV SERVER:"
echo "  After connecting, run: phstart"
echo "  This launches mprocs with all services."
echo "  (Requires interactive terminal - cannot auto-start in background)"
echo ""
echo "In mprocs, press 'r' on generate-demo-data to create test data."
echo ""
echo "Makefile commands: phmake help"
echo ""
'''
