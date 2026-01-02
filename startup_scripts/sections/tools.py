"""Developer tools: Claude Code, GitHub CLI, and OpenAI Codex CLI."""

from config import ClaudeCodeConfig, CodexCliConfig, GitHubCliConfig


def get_claude_code(claude_code: ClaudeCodeConfig) -> str:
    """Generate Claude Code install and configuration section (run after user creation)."""
    if not claude_code.enabled:
        return ""

    return f'''
section_start "Claude Code"

# Install Claude Code as ph user (installs to ~/.local/bin/claude)
su - ph -c "curl -fsSL https://claude.ai/install.sh | bash"

# Create Claude Code configuration directory
mkdir -p /home/ph/.claude

# Create settings.json with pre-approved permissions for headless use
cat > /home/ph/.claude/settings.json << 'CLAUDEEOF'
{{
  "permissions": {{
    "allow": ["Bash", "Read", "Edit", "Write", "Glob", "Grep", "WebFetch"]
  }}
}}
CLAUDEEOF

# Write secrets to a protected file instead of .bashrc
install -d -m 700 /home/ph/.config/posthog
claude_key=""
if [ -n "{claude_code.api_key_secret_name}" ]; then
    claude_key="$(fetch_secret "{claude_code.api_key_secret_name}" || true)"
fi
if [ -n "$claude_key" ]; then
    printf 'CLAUDE_CODE_API_KEY=%s\n' "$claude_key" >> /home/ph/.config/posthog/secrets.env
    chmod 600 /home/ph/.config/posthog/secrets.env
fi

# Set non-secret environment settings
cat >> /home/ph/.bashrc << 'CLAUDEENVEOF'

# Claude Code configuration
export DISABLE_AUTOUPDATER=1
export PATH="$HOME/.local/bin:$PATH"
CLAUDEENVEOF

# Install a global wrapper so `claude` works from any directory
cat > /usr/local/bin/claude << 'CLAUDEWRAPEOF'
#!/bin/bash
if [ "$(id -un)" = "ph" ]; then
    exec /home/ph/.local/bin/claude "$@"
fi
exec runuser -u ph -- /home/ph/.local/bin/claude "$@"
CLAUDEWRAPEOF
chmod 755 /usr/local/bin/claude

chown -R ph:ph /home/ph/.claude /home/ph/.config/posthog
section_end "Claude Code"
'''


def get_github_cli(github_cli: GitHubCliConfig) -> str:
    """Generate GitHub CLI install and configuration section."""
    if not github_cli.enabled:
        return ""

    # Base install script (always run if enabled)
    script = '''
section_start "GitHub CLI"

# Add GitHub CLI apt repository
mkdir -p -m 755 /etc/apt/keyrings
wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt-get update
apt-get install -y gh
'''

    # Add token configuration if provided
    if github_cli.token_secret_name:
        script += f'''
# Store GitHub token in secrets file
install -d -m 700 /home/ph/.config/posthog
gh_token=""
if [ -n "{github_cli.token_secret_name}" ]; then
    gh_token="$(fetch_secret "{github_cli.token_secret_name}" || true)"
fi
if [ -n "$gh_token" ]; then
    printf 'GH_TOKEN=%s\n' "$gh_token" >> /home/ph/.config/posthog/secrets.env
    chmod 600 /home/ph/.config/posthog/secrets.env
fi
chown -R ph:ph /home/ph/.config/posthog
'''

    script += '''
section_end "GitHub CLI"
'''
    return script


def get_codex_cli_config(codex_cli: CodexCliConfig) -> str:
    """Generate OpenAI Codex CLI configuration section (run after Flox activation)."""
    if not codex_cli.enabled:
        return ""

    return f'''
section_start "Codex CLI"

# Install system Node.js (Codex runs outside Flox)
if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# Install Codex CLI globally
npm install -g @openai/codex

# Store OpenAI API key in secrets file
install -d -m 700 /home/ph/.config/posthog
openai_key=""
if [ -n "{codex_cli.api_key_secret_name}" ]; then
    openai_key="$(fetch_secret "{codex_cli.api_key_secret_name}" || true)"
fi
if [ -n "$openai_key" ]; then
    printf 'OPENAI_API_KEY=%s\n' "$openai_key" >> /home/ph/.config/posthog/secrets.env
    chmod 600 /home/ph/.config/posthog/secrets.env
fi
chown -R ph:ph /home/ph/.config/posthog

section_end "Codex CLI"
'''
