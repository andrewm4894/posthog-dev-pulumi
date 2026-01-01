"""PostHog Development VM Pulumi Program.

Provisions GCP VMs pre-configured for PostHog local development.
Access is via Chrome Remote Desktop (no external ports needed for PostHog).
"""

import pulumi
from pulumi import Config

from config import load_claude_code_config, load_codex_cli_config, load_monitoring_config, load_remote_desktop_config, load_vm_configs
from network import create_network, create_ssh_firewall
from vm import create_dev_vm


def main():
    """Main entry point for the Pulumi program."""
    # Load configuration
    config = Config()
    gcp_config = Config("gcp")

    project = gcp_config.require("project")
    region = gcp_config.require("region")
    zone = gcp_config.get("zone") or f"{region}-b"

    # Load VM configurations from Pulumi config
    vm_configs = load_vm_configs(config)

    # Load monitoring configuration
    monitoring = load_monitoring_config(config)

    # Load Claude Code configuration
    claude_code = load_claude_code_config(config)

    # Load Remote Desktop configuration
    remote_desktop = load_remote_desktop_config(config)

    # Load Codex CLI configuration
    codex_cli = load_codex_cli_config(config)

    # Create shared network resources
    network = create_network("posthog-dev-network")

    # Create SSH firewall rule (only port needed - Chrome Remote Desktop uses Google's relay)
    ssh_firewall = create_ssh_firewall("posthog-dev-ssh", network)

    # Create VMs based on configuration
    for vm_config in vm_configs:
        vm = create_dev_vm(
            vm_config=vm_config,
            network=network,
            zone=zone,
            monitoring=monitoring,
            claude_code=claude_code,
            remote_desktop=remote_desktop,
            codex_cli=codex_cli,
        )

        # Export VM details
        pulumi.export(
            f"{vm_config.name}_external_ip",
            vm.network_interfaces[0].access_configs[0].nat_ip,
        )
        pulumi.export(
            f"{vm_config.name}_internal_ip",
            vm.network_interfaces[0].network_ip,
        )
        pulumi.export(
            f"{vm_config.name}_ssh_command",
            pulumi.Output.concat(
                "gcloud compute ssh ",
                vm.name,
                " --zone=",
                zone,
                " --project=",
                project,
            ),
        )

    # Export network info
    pulumi.export("network_name", network.name)


main()
