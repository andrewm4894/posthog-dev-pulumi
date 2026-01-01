"""Network and firewall configuration for PostHog dev VMs.

Note: Only SSH is exposed externally. PostHog services are accessed locally
via Chrome Remote Desktop (which uses Google's HTTPS relay, no firewall needed).
"""

from pulumi_gcp import compute


def create_network(name: str) -> compute.Network:
    """Create a VPC network for development VMs."""
    return compute.Network(
        name,
        auto_create_subnetworks=True,
        description="Network for PostHog development VMs",
    )


def create_ssh_firewall(name: str, network: compute.Network) -> compute.Firewall:
    """Create firewall rule for SSH access.

    SSH is always open from 0.0.0.0/0 for OS Login to work properly.
    """
    return compute.Firewall(
        name,
        network=network.self_link,
        description="Allow SSH for OS Login",
        allows=[
            compute.FirewallAllowArgs(
                protocol="tcp",
                ports=["22"],
            ),
        ],
        source_ranges=["0.0.0.0/0"],
        target_tags=["posthog-dev"],
    )
