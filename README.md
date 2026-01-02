# PostHog Development VMs on GCP

Pulumi project to provision Google Cloud VMs for PostHog local development.

## Features

- **One-command deployment**: Spin up fully configured PostHog dev VMs
- **Chrome Remote Desktop**: Secure access via Google's remote desktop (no ports exposed)
- **Branch support**: Deploy from master or any feature branch
- **Multiple VMs**: Run multiple dev environments simultaneously
- **Pre-configured**: Docker, Flox, Python, Node.js, pnpm, mprocs all installed
- **AI coding tools**: Claude Code and OpenAI Codex CLI pre-installed

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

# (Optional) Store RDP sudo password in Secret Manager
echo -n "YourSecurePassword" | gcloud secrets create rdp-password --data-file=-
pulumi config set rdpPasswordSecretName "rdp-password"

# (Optional) Store API keys in Secret Manager
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key --data-file=-
echo -n "sk-..." | gcloud secrets create openai-api-key --data-file=-

# Reference secret names in config (vms.yaml or Pulumi config)
pulumi config set anthropicSecretName "anthropic-api-key"
pulumi config set openaiSecretName "openai-api-key"

# Deploy
pulumi up
```

## Configuration

### vms.yaml (Recommended)

Edit `vms.yaml` to define your VMs:

```yaml
defaults:
  machine_type: e2-standard-8
  disk_size_gb: 100
  posthog_branch: master
  # Optional: use a custom GCE image for faster bootstraps
  # os_image: "projects/YOUR_PROJECT/global/images/posthog-dev-base-YYYYMMDD"

vms:
  - name: posthog-dev-1
    description: "PostHog development VM"

  - name: posthog-feature-x
    description: "Feature X development"
    posthog_branch: feature-x-branch
```

### Pulumi Config (Alternative)

```bash
# Single VM mode
pulumi config set vmName my-dev-vm
pulumi config set posthogBranch my-feature-branch
pulumi config set machineType e2-standard-4
pulumi config set diskSizeGb 150
```

### Secrets & User Config (via Secret Manager)

```bash
pulumi config set netdataClaimRooms "ROOM_ID"          # Optional: Netdata room ID

# Store secrets in Secret Manager
echo -n "PASSWORD" | gcloud secrets create rdp-password --data-file=-
echo -n "TOKEN" | gcloud secrets create netdata-claim-token --data-file=-
echo -n "KEY" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "KEY" | gcloud secrets create openai-api-key --data-file=-
echo -n "TOKEN" | gcloud secrets create github-token --data-file=-

# Reference secret names in config (vms.yaml or Pulumi config)
pulumi config set rdpPasswordSecretName "rdp-password"
pulumi config set netdataClaimTokenSecretName "netdata-claim-token"
pulumi config set anthropicSecretName "anthropic-api-key"
pulumi config set openaiSecretName "openai-api-key"
pulumi config set githubTokenSecretName "github-token"
```

Grant the VM service account access to the secrets (Secret Manager Secret Accessor), e.g.:
```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```

## Connecting to Your VM

### 1. Set up Chrome Remote Desktop (one-time)

```bash
# SSH into the VM (uses IAP tunneling - no external IP needed)
gcloud compute ssh posthog-dev-1 --tunnel-through-iap --zone=europe-west1-b

# Switch to the ph user
sudo su - ph

# Go to https://remotedesktop.google.com/headless
# Click "Begin" > "Next" > "Authorize"
# Copy the Debian Linux command and run it on the VM
# Set a PIN when prompted
```

### 2. Connect via Chrome Remote Desktop

1. Go to https://remotedesktop.google.com/access
2. Click on your VM
3. Enter your PIN
4. You're now in the XFCE desktop

### 3. Start PostHog

Open a terminal in the desktop and run:

```bash
phstart
```

This launches mprocs with all PostHog services. Access PostHog at `http://localhost:8010` in the VM's browser.

## Useful Commands

Once connected to the VM as the `ph` user:

```bash
phstart       # Start PostHog dev server (mprocs)
phattach      # Attach to running mprocs session
phtail        # Tail PostHog log files
phlogs        # View Docker container logs
phps          # Show Docker container status
phdown        # Stop Docker containers
phmake help   # Show all make commands
```

## Network Security

VMs have no external IP addresses. Access is via:
- **SSH**: IAP (Identity-Aware Proxy) tunneling - authenticated through your Google identity
- **Desktop**: Chrome Remote Desktop - uses Google's secure HTTPS relay

Cloud NAT provides outbound internet access for the VMs.

## Custom Base Images (Optional)

To speed up provisioning, you can bake a GCE image from a fully provisioned VM.
If `os_image` is not set, the default Ubuntu image is used (full bootstrap).

```bash
# Create an image from an existing VM
make bake-image VM=posthog-master IMAGE=posthog-dev-base

# Use it as the default image for new VMs (supports ${GCP_PROJECT})
pulumi config set baseImage "projects/${GCP_PROJECT}/global/images/posthog-dev-base"
```

When you bake an image, the VM is marked with `/etc/posthog-base-image`.
On boot, the startup script detects this marker and skips heavy steps
(repo clone, Flox activation, Docker services, and image pre-pull).

Refresh the image whenever you update startup scripts or dependencies.

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
gcloud compute ssh posthog-dev-1 --tunnel-through-iap --zone=europe-west1-b
sudo cat /var/log/posthog-startup.log
sudo cat /var/log/posthog-startup-timing.log
```

### Docker issues

```bash
sudo su - ph
docker compose -f ~/posthog/docker-compose.dev.yml ps
docker compose -f ~/posthog/docker-compose.dev.yml logs -f
```

### Chrome Remote Desktop not working

1. Make sure you ran the setup command from https://remotedesktop.google.com/headless
2. Check the service: `systemctl --user status chrome-remote-desktop`
3. Restart it: `systemctl --user restart chrome-remote-desktop`

## Cost Estimate

| Resource | Cost (24/7) | Notes |
|----------|-------------|-------|
| e2-standard-8 VM | ~$200/month | Stop when not in use! |
| e2-standard-4 VM | ~$100/month | Lighter workloads |
| 100GB SSD | ~$17/month | - |

**Tip**: Stop VMs when not in use to save costs:
```bash
gcloud compute instances stop posthog-dev-1 --zone=europe-west1-b
gcloud compute instances start posthog-dev-1 --zone=europe-west1-b
```
