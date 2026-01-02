"""Modular startup script sections for PostHog development VMs."""

from .base import get_system_updates, get_docker_install, get_flox_install, get_system_deps, get_user_creation
from .monitoring import get_ops_agent_install, get_netdata_install
from .tools import get_claude_code, get_codex_cli_config
from .remote_desktop import get_remote_desktop_install, get_remote_desktop_config
from .posthog import (
    get_clone_repos,
    get_posthog_env,
    get_hosts_config,
    get_flox_activate,
    get_docker_services,
    get_start_script,
)
from .shell import get_makefile, get_bashrc, get_sysctl_and_docker_pull, get_final_message

__all__ = [
    # Base
    "get_system_updates",
    "get_docker_install",
    "get_flox_install",
    "get_system_deps",
    "get_user_creation",
    # Monitoring
    "get_ops_agent_install",
    "get_netdata_install",
    # Tools
    "get_claude_code",
    "get_codex_cli_config",
    # Remote Desktop
    "get_remote_desktop_install",
    "get_remote_desktop_config",
    # PostHog
    "get_clone_repos",
    "get_posthog_env",
    "get_hosts_config",
    "get_flox_activate",
    "get_docker_services",
    "get_start_script",
    # Shell
    "get_makefile",
    "get_bashrc",
    "get_sysctl_and_docker_pull",
    "get_final_message",
]
