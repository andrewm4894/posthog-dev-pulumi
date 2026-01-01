# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Pulumi Python project that provisions GCP VMs pre-configured for PostHog local development. VMs are created with Docker, Flox, Node.js, Python, and all dependencies needed to run PostHog.

## Common Commands

```bash
# Install dependencies
uv sync

# Deploy VMs
pulumi up

# Preview changes
pulumi preview

# Destroy infrastructure
pulumi destroy

# Create a new VM stack
make new-vm NAME=my-feature BRANCH=feature-branch

# List all stacks
make stacks

# SSH into a VM (uses IAP tunneling)
make ssh VM=posthog-dev-1

# Stop/start VMs to save costs
make stop-vm VM=posthog-dev-1
make start-vm VM=posthog-dev-1

# View startup script logs
make logs VM=posthog-dev-1
```

## Configuration

VMs can be configured in two ways:
1. **vms.yaml** (recommended) - Edit the `vms` array to define VMs with their settings
2. **Pulumi config** - Use `pulumi config set` for individual settings

Secrets and user-specific config must be stored via Pulumi (not in vms.yaml):
```bash
pulumi config set netdataClaimRooms "ROOM_ID"            # Your Netdata room ID
pulumi config set --secret netdataClaimToken "TOKEN"     # Netdata claim token
pulumi config set --secret anthropicApiKey "KEY"         # Claude Code API key
pulumi config set --secret openaiApiKey "KEY"            # Codex CLI API key
pulumi config set --secret rdpPassword "PASSWORD"        # For sudo in Chrome Remote Desktop
```

## Architecture

```
__main__.py          # Entry point - orchestrates VM creation
config.py            # Configuration loading from vms.yaml and Pulumi config
                     # Dataclasses: VMConfig, MonitoringConfig, ClaudeCodeConfig, RemoteDesktopConfig
network.py           # VPC network, Cloud NAT, IAP firewall (no external IPs)
vm.py                # GCP compute instance creation
constants.py         # Version pins (Flox), Docker config, sysctl settings
startup_scripts/
  full_startup.py    # Generates bash startup script for VM provisioning
vms.yaml             # VM definitions and default settings (not for secrets)
```

**Flow**: `__main__.py` loads config from `vms.yaml` via `config.py`, creates network resources via `network.py`, then creates VMs via `vm.py` which uses `startup_scripts/full_startup.py` to generate the bash provisioning script.

## Key Patterns

- Configuration priority: vms.yaml > Pulumi config JSON arrays > Pulumi config individual keys
- VMs have no external IPs for security; access is via:
  - **SSH**: IAP (Identity-Aware Proxy) tunneling (`gcloud compute ssh VM --tunnel-through-iap`)
  - **Desktop**: Chrome Remote Desktop (uses Google's relay, no firewall needed)
- Cloud NAT provides outbound internet access for package downloads, CRD relay, etc.
- Startup scripts install: GCP Ops Agent, Netdata, Docker, Flox, Claude Code, Chrome Remote Desktop + XFCE
- VMs use Flox for dependency management (PostHog's recommended approach)
- Network tag `posthog-dev` is used for firewall rules
