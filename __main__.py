"""PostHog Development VM Pulumi Program.

Provisions GCP VMs pre-configured for PostHog local development.
"""

import pulumi
from pulumi import Config

from config import load_allowed_ips, load_vm_configs
from network import create_network, create_posthog_firewall, create_ssh_firewall
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

    # Load allowed IPs for firewall
    allowed_ips = load_allowed_ips(config)

    # Create shared network resources
    network = create_network("posthog-dev-network")

    # Create firewall rules
    ssh_firewall = create_ssh_firewall("posthog-dev-ssh", network)
    posthog_firewall = create_posthog_firewall(
        "posthog-dev-services",
        network,
        allowed_ips,
    )

    # Create VMs based on configuration
    for vm_config in vm_configs:
        vm = create_dev_vm(
            vm_config=vm_config,
            network=network,
            zone=zone,
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
        pulumi.export(
            f"{vm_config.name}_posthog_url",
            pulumi.Output.concat(
                "http://",
                vm.network_interfaces[0].access_configs[0].nat_ip,
                ":8010",
            ),
        )

    # Export network info
    pulumi.export("network_name", network.name)
    pulumi.export("allowed_ips", allowed_ips)


main()
