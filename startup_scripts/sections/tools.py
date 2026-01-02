"""Developer tools: Claude Code, GitHub CLI, and OpenAI Codex CLI."""

from config import ClaudeCodeConfig, CodexCliConfig, GitHubCliConfig


def get_claude_code(claude_code: ClaudeCodeConfig) -> str:
    """Generate Claude Code install and configuration section (run after user creation)."""
    if not claude_code.enabled or not claude_code.api_key:
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

# Set environment variables for headless use
cat >> /home/ph/.bashrc << 'CLAUDEENVEOF'

# Claude Code configuration
export CLAUDE_CODE_API_KEY="{claude_code.api_key}"
export DISABLE_AUTOUPDATER=1
export PATH="$HOME/.local/bin:$PATH"
CLAUDEENVEOF

chown -R ph:ph /home/ph/.claude
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
    if github_cli.token:
        script += f'''
# Set GitHub token for authentication
cat >> /home/ph/.bashrc << 'GHENVEOF'

# GitHub CLI configuration
export GH_TOKEN="{github_cli.token}"
GHENVEOF
'''

    script += '''
section_end "GitHub CLI"
'''
    return script


def get_codex_cli_config(codex_cli: CodexCliConfig) -> str:
    """Generate OpenAI Codex CLI configuration section (run after Flox activation)."""
    if not codex_cli.enabled or not codex_cli.api_key:
        return ""

    return f'''
section_start "Codex CLI"

# Install Codex CLI globally using npm (available via Flox)
su - ph -c "cd /home/ph/posthog && FLOX_NO_DIRENV_SETUP=1 flox activate -- npm install -g @openai/codex" || true

# Set environment variable for API key in user's profile
cat >> /home/ph/.bashrc << 'CODEXENVEOF'

# OpenAI Codex CLI configuration
export OPENAI_API_KEY="{codex_cli.api_key}"
CODEXENVEOF

section_end "Codex CLI"
'''
