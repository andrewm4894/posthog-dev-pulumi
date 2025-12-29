"""Configuration loading and validation for PostHog dev VMs."""

from dataclasses import dataclass, field
import json
from typing import Optional

from pulumi import Config


@dataclass
class RepoConfig:
    """Configuration for a repository to clone."""

    url: str
    branch: str = "master"
    target_dir: Optional[str] = None

    def __post_init__(self):
        if self.target_dir is None:
            # Extract repo name from URL
            self.target_dir = self.url.rstrip("/").split("/")[-1].replace(".git", "")


@dataclass
class VMConfig:
    """Configuration for a single development VM."""

    name: str
    description: str = ""
    machine_type: str = "e2-standard-8"
    disk_size_gb: int = 100
    os_image: str = "ubuntu-os-cloud/ubuntu-2204-lts"
    posthog_branch: str = "master"
    additional_repos: list[RepoConfig] = field(default_factory=list)
    enable_minimal_mode: bool = False
    labels: dict[str, str] = field(default_factory=dict)


def load_vm_configs(config: Config) -> list[VMConfig]:
    """Load VM configurations from Pulumi config.

    Supports two modes:
    1. Single VM mode: Use individual config keys
    2. Multi-VM mode: Use 'vms' JSON array config

    Returns:
        List of VMConfig objects
    """
    # Check for multi-VM configuration
    vms_json = config.get("vms")
    if vms_json:
        vms_data = json.loads(vms_json)
        return [_parse_vm_config(vm) for vm in vms_data]

    # Single VM mode - use individual config keys
    name = config.get("vmName") or "posthog-dev-1"
    description = config.get("vmDescription") or "PostHog development VM"
    machine_type = config.get("machineType") or "e2-standard-8"
    disk_size_gb = int(config.get("diskSizeGb") or "100")
    os_image = config.get("osImage") or "ubuntu-os-cloud/ubuntu-2204-lts"
    posthog_branch = config.get("posthogBranch") or "master"
    enable_minimal = config.get_bool("enableMinimalMode") or False

    # Parse additional repos if provided
    additional_repos = []
    repos_json = config.get("additionalRepos")
    if repos_json:
        repos_data = json.loads(repos_json)
        additional_repos = [RepoConfig(**r) for r in repos_data]

    return [
        VMConfig(
            name=name,
            description=description,
            machine_type=machine_type,
            disk_size_gb=disk_size_gb,
            os_image=os_image,
            posthog_branch=posthog_branch,
            additional_repos=additional_repos,
            enable_minimal_mode=enable_minimal,
        )
    ]


def load_allowed_ips(config: Config) -> list[str]:
    """Load allowed IP CIDRs from config.

    Returns:
        List of IP CIDR strings (e.g., ["1.2.3.4/32"])
    """
    ips_json = config.get("allowedIps")
    if ips_json:
        return json.loads(ips_json)
    # Default: open to all
    return ["0.0.0.0/0"]


def _parse_vm_config(data: dict) -> VMConfig:
    """Parse a VM configuration from a dictionary."""
    additional_repos = [RepoConfig(**r) for r in data.get("additional_repos", [])]
    return VMConfig(
        name=data["name"],
        description=data.get("description", ""),
        machine_type=data.get("machine_type", "e2-standard-8"),
        disk_size_gb=data.get("disk_size_gb", 100),
        os_image=data.get("os_image", "ubuntu-os-cloud/ubuntu-2204-lts"),
        posthog_branch=data.get("posthog_branch", "master"),
        additional_repos=additional_repos,
        enable_minimal_mode=data.get("enable_minimal_mode", False),
        labels=data.get("labels", {}),
    )
