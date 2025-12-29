"""Constants and version pins for PostHog dev VM provisioning."""

# Flox - PostHog's recommended dev environment manager
# See: https://flox.dev/docs/install-flox/install/
FLOX_VERSION = "1.8.0"

# Docker daemon configuration
DOCKER_CONFIG = {
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3",
    },
    "storage-driver": "overlay2",
}

# System limits for Docker/ClickHouse
SYSCTL_SETTINGS = {
    "vm.max_map_count": 262144,
    "fs.file-max": 65536,
}

# Default PostHog environment variables
POSTHOG_ENV_DEFAULTS = {
    "DEBUG": "1",
    "SKIP_SERVICE_VERSION_REQUIREMENTS": "1",
    "SECRET_KEY": "dev-secret-key-not-for-production",
    "DATABASE_URL": "postgres://posthog:posthog@localhost:5432/posthog",
    "REDIS_URL": "redis://localhost:6379/",
    "CLICKHOUSE_HOST": "localhost",
}

# Default mprocs config for file-based logging (useful for code agents)
DEFAULT_MPROCS_CONFIG = "bin/mprocs-with-logging.yaml"
