"""Configuration loading and validation for PostHog dev VMs."""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Optional

import yaml
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


@dataclass
class MonitoringConfig:
    """Configuration for monitoring agents."""

    ops_agent_enabled: bool = True
    netdata_enabled: bool = False
    netdata_claim_url: str = ""
    netdata_claim_rooms: str = ""
    netdata_claim_token: str = ""  # Loaded from Pulumi secret


@dataclass
class VMsYamlConfig:
    """Configuration loaded from vms.yaml file."""

    defaults: dict
    vms: list[dict]
    monitoring: dict


def _load_yaml_config() -> Optional[VMsYamlConfig]:
    """Load configuration from vms.yaml if it exists."""
    yaml_path = Path(__file__).parent / "vms.yaml"
    if not yaml_path.exists():
        return None

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    return VMsYamlConfig(
        defaults=data.get("defaults", {}),
        vms=data.get("vms", []),
        monitoring=data.get("monitoring", {}),
    )


def load_vm_configs(config: Config) -> list[VMConfig]:
    """Load VM configurations from vms.yaml or Pulumi config.

    Priority:
    1. vms.yaml file (recommended)
    2. Pulumi config 'vms' JSON array
    3. Pulumi config individual keys (single VM mode)

    Returns:
        List of VMConfig objects
    """
    # First, try loading from vms.yaml
    yaml_config = _load_yaml_config()
    if yaml_config and yaml_config.vms:
        defaults = yaml_config.defaults
        return [_parse_vm_config(vm, defaults) for vm in yaml_config.vms]

    # Check for multi-VM configuration in Pulumi config
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
    """Load allowed IP CIDRs from Pulumi config only.

    NOTE: IPs should NOT be stored in vms.yaml (it's in git).
    Use: pulumi config set allowedIps '["YOUR.IP/32"]'

    Returns:
        List of IP CIDR strings (e.g., ["1.2.3.4/32"])

    Raises:
        ValueError: If no allowed IPs are configured (security requirement)
    """
    ips_json = config.get("allowedIps")
    if ips_json:
        return json.loads(ips_json)

    raise ValueError(
        "No allowed IPs configured! This is required for security.\n"
        "Run: pulumi config set allowedIps '[\"YOUR.IP.HERE/32\"]'\n"
        "Find your IP at: https://whatismyip.com"
    )


def load_monitoring_config(config: Config) -> MonitoringConfig:
    """Load monitoring configuration from vms.yaml and Pulumi secrets.

    Returns:
        MonitoringConfig with agent settings
    """
    yaml_config = _load_yaml_config()
    monitoring = yaml_config.monitoring if yaml_config else {}

    # Netdata claim token is stored as a Pulumi secret (use get() for plain value)
    # The value is still encrypted in the state file
    netdata_claim_token = config.get("netdataClaimToken") or ""

    return MonitoringConfig(
        ops_agent_enabled=monitoring.get("ops_agent_enabled", True),
        netdata_enabled=monitoring.get("netdata_enabled", False),
        netdata_claim_url=monitoring.get("netdata_claim_url", "https://app.netdata.cloud"),
        netdata_claim_rooms=monitoring.get("netdata_claim_rooms", ""),
        netdata_claim_token=netdata_claim_token,
    )


def _parse_vm_config(data: dict, defaults: Optional[dict] = None) -> VMConfig:
    """Parse a VM configuration from a dictionary, with optional defaults."""
    defaults = defaults or {}
    additional_repos = [RepoConfig(**r) for r in data.get("additional_repos", [])]

    # Helper to get value with fallback to defaults
    def get(key: str, fallback):
        return data.get(key) if data.get(key) is not None else defaults.get(key, fallback)

    return VMConfig(
        name=data["name"],
        description=data.get("description", ""),
        machine_type=get("machine_type", "e2-standard-8"),
        disk_size_gb=get("disk_size_gb", 100),
        os_image=get("os_image", "ubuntu-os-cloud/ubuntu-2204-lts"),
        posthog_branch=get("posthog_branch", "master"),
        additional_repos=additional_repos,
        enable_minimal_mode=get("enable_minimal_mode", False),
        labels=data.get("labels", {}),
    )
