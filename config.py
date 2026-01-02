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
class ClaudeCodeConfig:
    """Configuration for Claude Code installation."""

    enabled: bool = True
    api_key: str = ""  # Loaded from Pulumi secret


@dataclass
class RemoteDesktopConfig:
    """Configuration for Chrome Remote Desktop access."""

    enabled: bool = True
    password: str = ""  # Loaded from Pulumi secret (used for sudo in desktop session)


@dataclass
class CodexCliConfig:
    """Configuration for OpenAI Codex CLI installation."""

    enabled: bool = True
    api_key: str = ""  # Loaded from Pulumi secret


@dataclass
class GitHubCliConfig:
    """Configuration for GitHub CLI installation."""

    enabled: bool = True
    token: str = ""  # Loaded from Pulumi secret


@dataclass
class VMsYamlConfig:
    """Configuration loaded from vms.yaml file."""

    defaults: dict
    vms: list[dict]
    monitoring: dict
    claude_code: dict
    remote_desktop: dict
    codex_cli: dict
    github_cli: dict


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
        claude_code=data.get("claude_code", {}),
        remote_desktop=data.get("remote_desktop", {}),
        codex_cli=data.get("codex_cli", {}),
        github_cli=data.get("github_cli", {}),
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


def load_monitoring_config(config: Config) -> MonitoringConfig:
    """Load monitoring configuration from vms.yaml and Pulumi secrets.

    Returns:
        MonitoringConfig with agent settings
    """
    yaml_config = _load_yaml_config()
    monitoring = yaml_config.monitoring if yaml_config else {}

    # Netdata settings from Pulumi config (token is a secret)
    netdata_claim_token = config.get("netdataClaimToken") or ""
    netdata_claim_rooms = config.get("netdataClaimRooms") or ""

    return MonitoringConfig(
        ops_agent_enabled=monitoring.get("ops_agent_enabled", True),
        netdata_enabled=monitoring.get("netdata_enabled", False),
        netdata_claim_url=monitoring.get("netdata_claim_url", "https://app.netdata.cloud"),
        netdata_claim_rooms=netdata_claim_rooms,
        netdata_claim_token=netdata_claim_token,
    )


def load_claude_code_config(config: Config) -> ClaudeCodeConfig:
    """Load Claude Code configuration from vms.yaml and Pulumi secrets.

    Returns:
        ClaudeCodeConfig with Claude Code settings
    """
    yaml_config = _load_yaml_config()
    claude_code = yaml_config.claude_code if yaml_config else {}

    # API key is stored as a Pulumi secret
    api_key = config.get("anthropicApiKey") or ""

    return ClaudeCodeConfig(
        enabled=claude_code.get("enabled", True),
        api_key=api_key,
    )


def load_remote_desktop_config(config: Config) -> RemoteDesktopConfig:
    """Load Chrome Remote Desktop configuration from vms.yaml and Pulumi secrets.

    Returns:
        RemoteDesktopConfig with Chrome Remote Desktop settings
    """
    yaml_config = _load_yaml_config()
    remote_desktop = yaml_config.remote_desktop if yaml_config else {}

    # Password is stored as a Pulumi secret (used for sudo in desktop session)
    password = config.get("rdpPassword") or ""

    return RemoteDesktopConfig(
        enabled=remote_desktop.get("enabled", True),
        password=password,
    )


def load_codex_cli_config(config: Config) -> CodexCliConfig:
    """Load OpenAI Codex CLI configuration from vms.yaml and Pulumi secrets.

    Returns:
        CodexCliConfig with Codex CLI settings
    """
    yaml_config = _load_yaml_config()
    codex_cli = yaml_config.codex_cli if yaml_config else {}

    # API key is stored as a Pulumi secret
    api_key = config.get("openaiApiKey") or ""

    return CodexCliConfig(
        enabled=codex_cli.get("enabled", True),
        api_key=api_key,
    )


def load_github_cli_config(config: Config) -> GitHubCliConfig:
    """Load GitHub CLI configuration from vms.yaml and Pulumi secrets.

    Returns:
        GitHubCliConfig with GitHub CLI settings
    """
    yaml_config = _load_yaml_config()
    github_cli = yaml_config.github_cli if yaml_config else {}

    # Token is stored as a Pulumi secret
    token = config.get("githubToken") or ""

    return GitHubCliConfig(
        enabled=github_cli.get("enabled", True),
        token=token,
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
