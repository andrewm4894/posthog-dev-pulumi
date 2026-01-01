"""Network and firewall configuration for PostHog dev VMs.

VMs have no external IPs for security. Access is via:
- SSH: IAP (Identity-Aware Proxy) tunneling
- Desktop: Chrome Remote Desktop (uses Google's HTTPS relay, no firewall needed)

Outbound internet access is provided via Cloud NAT.
"""

from pulumi_gcp import compute

# IAP's IP range for SSH tunneling
# https://cloud.google.com/iap/docs/using-tcp-forwarding#create-firewall-rule
IAP_IP_RANGE = "35.235.240.0/20"


def create_network(name: str) -> compute.Network:
    """Create a VPC network for development VMs."""
    return compute.Network(
        name,
        auto_create_subnetworks=True,
        description="Network for PostHog development VMs",
    )


def create_cloud_router(name: str, network: compute.Network, region: str) -> compute.Router:
    """Create a Cloud Router for NAT gateway."""
    return compute.Router(
        name,
        network=network.id,
        region=region,
        description="Router for PostHog dev VMs NAT",
    )


def create_cloud_nat(name: str, router: compute.Router, region: str) -> compute.RouterNat:
    """Create Cloud NAT for outbound internet access.

    Required since VMs don't have external IPs.
    """
    return compute.RouterNat(
        name,
        router=router.name,
        region=region,
        nat_ip_allocate_option="AUTO_ONLY",
        source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES",
        log_config=compute.RouterNatLogConfigArgs(
            enable=True,
            filter="ERRORS_ONLY",
        ),
    )


def create_iap_ssh_firewall(name: str, network: compute.Network) -> compute.Firewall:
    """Create firewall rule for SSH via IAP tunneling.

    Only allows SSH from Google's IAP IP range, not the public internet.
    Use: gcloud compute ssh VM_NAME --tunnel-through-iap
    """
    return compute.Firewall(
        name,
        network=network.self_link,
        description="Allow SSH from IAP for secure tunneling",
        allows=[
            compute.FirewallAllowArgs(
                protocol="tcp",
                ports=["22"],
            ),
        ],
        source_ranges=[IAP_IP_RANGE],
        target_tags=["posthog-dev"],
    )
