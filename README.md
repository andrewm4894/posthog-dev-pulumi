# PostHog Development VMs on GCP

Pulumi project to provision Google Cloud VMs for PostHog local development.

## Features

- **One-command deployment**: Spin up fully configured PostHog dev VMs
- **Branch support**: Deploy from master or any feature branch
- **Multiple VMs**: Run multiple dev environments simultaneously
- **IP restriction**: Lock down access to your home/office IP
- **Pre-configured**: Docker, Python 3.12, Node 20, pnpm, mprocs all installed
- **Ready to run**: Just SSH in and run `./bin/start`

## Prerequisites

1. **Pulumi CLI**: `brew install pulumi`
2. **Pulumi Cloud account**: `pulumi login` (free for individuals)
3. **gcloud CLI**: Installed and authenticated with `gcloud auth login`
4. **GCP Project**: With Compute Engine API enabled

## Quick Start

```bash
# Clone this repo
git clone https://github.com/andrewm4894/posthog-dev-pulumi.git
cd posthog-dev-pulumi

# Install dependencies
uv sync

# Select the dev stack
pulumi stack select dev

# Configure GCP project and region
pulumi config set gcp:project YOUR_PROJECT_ID
pulumi config set gcp:region europe-west1

# (Recommended) Restrict access to your IP
pulumi config set allowedIps '["YOUR.HOME.IP/32"]'

# Deploy
pulumi up
```

## Configuration Options

### Single VM Mode

```bash
# VM name and description
pulumi config set vmName my-dev-vm
pulumi config set vmDescription "My PostHog development VM"

# Branch to checkout (default: master)
pulumi config set posthogBranch my-feature-branch

# Machine type (default: e2-standard-8)
pulumi config set machineType e2-standard-4

# Disk size in GB (default: 100)
pulumi config set diskSizeGb 150

# Enable minimal mode (fewer services, less RAM)
pulumi config set enableMinimalMode true

# Restrict to your IP (find it at whatismyip.com)
pulumi config set allowedIps '["1.2.3.4/32"]'
```

### Multiple VMs

```bash
pulumi config set vms '[
  {
    "name": "dev-vm-1",
    "description": "Feature branch A",
    "posthog_branch": "feature-a",
    "enable_minimal_mode": false
  },
  {
    "name": "dev-vm-2",
    "description": "Feature branch B",
    "posthog_branch": "feature-b",
    "enable_minimal_mode": true
  }
]'
```

### Additional Repositories

```bash
pulumi config set additionalRepos '[
  {"url": "https://github.com/posthog/posthog.com", "branch": "master"},
  {"url": "https://github.com/posthog/plugin-server", "branch": "main"}
]'
```

## SSH Access

Uses GCP OS Login - SSH with your Google account:

```bash
# Get SSH command from Pulumi outputs
pulumi stack output posthog-dev-1_ssh_command

# Or directly:
gcloud compute ssh posthog-dev-1 --zone=europe-west1-b --project=YOUR_PROJECT
```

## Using the VM

```bash
# SSH into VM
gcloud compute ssh posthog-dev-1 --zone=europe-west1-b

# Switch to development user
sudo su - ph

# Start PostHog (full mode)
./bin/start

# Or start in minimal mode (lighter resource usage)
./bin/start --minimal

# Convenience aliases available:
# phstart   - Start PostHog (full mode)
# phminimal - Start PostHog (minimal mode)
# phlogs    - View Docker container logs
# phps      - Show Docker container status
# phdown    - Stop Docker containers
```

Access PostHog at `http://<external-ip>:8010`

## Ports Exposed

| Port  | Service            | Notes                    |
|-------|-------------------|--------------------------|
| 22    | SSH               | Always open (OS Login)   |
| 8010  | PostHog (main)    | Via Caddy proxy          |
| 8000  | Backend           | Direct access            |
| 3000  | Frontend          | Vite dev server          |
| 8123  | ClickHouse        | HTTP interface           |
| 5555  | Flower            | Celery monitoring        |
| 16686 | Jaeger            | Tracing (full mode only) |
| 8081  | Temporal UI       | Workflows (full mode)    |
| 3030  | Dagster UI        | Pipelines (full mode)    |

## Cleanup

```bash
# Destroy all resources
pulumi destroy

# Remove stack (optional)
pulumi stack rm dev
```

## Troubleshooting

### Startup script logs

```bash
# SSH into VM and check logs
sudo cat /var/log/posthog-startup.log
sudo journalctl -u google-startup-scripts
```

### Docker not starting

```bash
sudo systemctl status docker
sudo systemctl restart docker
```

### PostHog not accessible

1. Check firewall rules allow your IP: `pulumi stack output allowed_ips`
2. Verify VM is running: `gcloud compute instances list`
3. Check if startup script completed: `cat /var/log/posthog-startup.log`

## Cost Estimate

| Resource | Cost (24/7) | Notes |
|----------|-------------|-------|
| e2-standard-8 VM | ~$200/month | Stop when not in use! |
| e2-standard-4 VM | ~$100/month | Minimal mode recommended |
| 100GB SSD | ~$17/month | - |
| Network egress | Variable | Minimal for dev |

**Tip**: Stop VMs when not in use to save costs:
```bash
gcloud compute instances stop posthog-dev-1 --zone=europe-west1-b
```
