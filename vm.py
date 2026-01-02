"""VM resource definitions for PostHog development."""

from pulumi import ResourceOptions
from pulumi_gcp import compute

from config import ClaudeCodeConfig, CodexCliConfig, GitConfig, GitHubCliConfig, MonitoringConfig, RemoteDesktopConfig, VMConfig
from startup_scripts.full_startup import generate_startup_script


def create_dev_vm(
    vm_config: VMConfig,
    network: compute.Network,
    zone: str,
    monitoring: MonitoringConfig | None = None,
    claude_code: ClaudeCodeConfig | None = None,
    github_cli: GitHubCliConfig | None = None,
    git_config: GitConfig | None = None,
    remote_desktop: RemoteDesktopConfig | None = None,
    codex_cli: CodexCliConfig | None = None,
) -> compute.Instance:
    """Create a development VM for PostHog.

    Args:
        vm_config: VM configuration
        network: VPC network to attach to
        zone: GCP zone for the VM
        monitoring: Monitoring agents configuration
        claude_code: Claude Code installation configuration
        github_cli: GitHub CLI installation configuration
        git_config: Git identity configuration
        remote_desktop: Remote desktop (xrdp) configuration
        codex_cli: OpenAI Codex CLI installation configuration

    Returns:
        The created compute instance
    """
    # Generate the startup script based on configuration
    startup_script = generate_startup_script(
        posthog_branch=vm_config.posthog_branch,
        additional_repos=vm_config.additional_repos,
        enable_minimal_mode=vm_config.enable_minimal_mode,
        monitoring=monitoring,
        claude_code=claude_code,
        github_cli=github_cli,
        git_config=git_config,
        remote_desktop=remote_desktop,
        codex_cli=codex_cli,
    )

    # Prepare labels
    labels = {
        "purpose": "posthog-dev",
        "managed-by": "pulumi",
        "branch": vm_config.posthog_branch.replace("/", "-").replace("_", "-").lower(),
        **vm_config.labels,
    }

    return compute.Instance(
        vm_config.name,
        name=vm_config.name,
        machine_type=vm_config.machine_type,
        zone=zone,
        description=vm_config.description,
        tags=["posthog-dev"],
        labels=labels,
        boot_disk=compute.InstanceBootDiskArgs(
            initialize_params=compute.InstanceBootDiskInitializeParamsArgs(
                image=vm_config.os_image,
                size=vm_config.disk_size_gb,
                type="pd-ssd",
                labels=labels,
            ),
            auto_delete=True,
        ),
        network_interfaces=[
            compute.InstanceNetworkInterfaceArgs(
                network=network.id,
                # No external IP - use IAP tunneling for SSH, Cloud NAT for outbound
            )
        ],
        # Enable OS Login for simple SSH access
        metadata={
            "enable-oslogin": "TRUE",
        },
        # Startup script runs on first boot
        metadata_startup_script=startup_script,
        # Service account with minimal permissions
        service_account=compute.InstanceServiceAccountArgs(
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        ),
        # Allow stopping for updates (e.g., changing machine type)
        allow_stopping_for_update=True,
        # Deletion protection off for dev VMs
        deletion_protection=False,
        opts=ResourceOptions(delete_before_replace=True),
    )
