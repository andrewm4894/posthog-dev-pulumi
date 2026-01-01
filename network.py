"""Network and firewall configuration for PostHog dev VMs."""

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


def create_posthog_firewall(
    name: str,
    network: compute.Network,
    allowed_ips: list[str],
) -> compute.Firewall:
    """Create firewall rules for PostHog services.

    Args:
        name: Firewall rule name
        network: VPC network to attach to
        allowed_ips: List of IP CIDRs allowed to access PostHog ports

    Opens ports:
    - 8010: PostHog main app (via Caddy proxy)
    - 8000: PostHog backend (direct)
    - 8234: Frontend Vite dev server (for external JS loading)
    - 3000: Frontend dev server (alternate port)
    - 8123: ClickHouse HTTP
    - 5555: Flower (Celery monitoring)
    - 1080: Maildev
    - 16686: Jaeger UI (tracing)
    - 8081: Temporal UI
    - 3030: Dagster UI
    - 9093: Kafka UI
    """
    return compute.Firewall(
        name,
        network=network.self_link,
        description="Allow traffic for PostHog development services",
        allows=[
            # PostHog core services
            compute.FirewallAllowArgs(
                protocol="tcp",
                ports=[
                    "8010",  # Main app (Caddy proxy)
                    "8000",  # Backend direct
                    "8234",  # Frontend Vite dev server (JS/assets for external access)
                    "3000",  # Frontend dev server (alternate)
                ],
            ),
            # Development/debugging services
            compute.FirewallAllowArgs(
                protocol="tcp",
                ports=[
                    "8123",  # ClickHouse HTTP
                    "5555",  # Flower
                    "1080",  # Maildev
                    "16686",  # Jaeger UI
                    "8081",  # Temporal UI
                    "3030",  # Dagster UI
                    "9093",  # Kafka UI
                ],
            ),
            # ICMP for ping/diagnostics
            compute.FirewallAllowArgs(
                protocol="icmp",
            ),
        ],
        source_ranges=allowed_ips,
        target_tags=["posthog-dev"],
    )


def create_rdp_firewall(
    name: str,
    network: compute.Network,
    allowed_ips: list[str],
    allow_all_ips: bool = False,
) -> compute.Firewall:
    """Create firewall rule for RDP (xrdp) access.

    Args:
        name: Firewall rule name
        network: VPC network to attach to
        allowed_ips: List of IP CIDRs allowed to access RDP
        allow_all_ips: If True, allow RDP from anywhere (0.0.0.0/0)

    Opens port 3389 for xrdp remote desktop.
    """
    source_ranges = ["0.0.0.0/0"] if allow_all_ips else allowed_ips

    return compute.Firewall(
        name,
        network=network.self_link,
        description="Allow RDP (xrdp) remote desktop access",
        allows=[
            compute.FirewallAllowArgs(
                protocol="tcp",
                ports=["3389"],
            ),
        ],
        source_ranges=source_ranges,
        target_tags=["posthog-dev"],
    )
