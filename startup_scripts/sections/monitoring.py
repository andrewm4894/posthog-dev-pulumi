"""Monitoring agents: GCP Ops Agent and Netdata."""

from config import MonitoringConfig


def get_ops_agent_install(monitoring: MonitoringConfig) -> str:
    """Generate GCP Ops Agent installation section."""
    if not monitoring.ops_agent_enabled:
        return ""

    return '''
section_start "GCP Ops Agent"
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
bash add-google-cloud-ops-agent-repo.sh --also-install
rm add-google-cloud-ops-agent-repo.sh
systemctl enable google-cloud-ops-agent
section_end "GCP Ops Agent"
'''


def get_netdata_install(monitoring: MonitoringConfig) -> str:
    """Generate Netdata installation section."""
    if not monitoring.netdata_enabled or not monitoring.netdata_claim_token:
        return ""

    return f'''
section_start "Netdata"
wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh
sh /tmp/netdata-kickstart.sh --stable-channel --non-interactive \\
    --claim-token {monitoring.netdata_claim_token} \\
    --claim-rooms {monitoring.netdata_claim_rooms} \\
    --claim-url {monitoring.netdata_claim_url}
rm /tmp/netdata-kickstart.sh
section_end "Netdata"
'''
