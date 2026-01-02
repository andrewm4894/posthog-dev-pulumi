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
    if not monitoring.netdata_enabled:
        return ""

    return f'''
section_start "Netdata"
if [ "$SKIP_HEAVY" = "1" ]; then
    echo "Skipping Netdata install (base image detected)"
    section_end "Netdata"
else
    wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh
    netdata_token=""
    if [ -n "{monitoring.netdata_claim_token_secret_name}" ]; then
        netdata_token="$(fetch_secret "{monitoring.netdata_claim_token_secret_name}" || true)"
    fi
    if [ -n "$netdata_token" ]; then
        NETDATA_CLAIM_TOKEN="$netdata_token" \\
        NETDATA_CLAIM_ROOMS="{monitoring.netdata_claim_rooms}" \\
        NETDATA_CLAIM_URL="{monitoring.netdata_claim_url}" \\
            sh /tmp/netdata-kickstart.sh --stable-channel --non-interactive
    else
        echo "Netdata claim token not set; skipping Netdata claim."
    fi
    rm /tmp/netdata-kickstart.sh
    section_end "Netdata"
fi
'''
