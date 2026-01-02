"""Developer tools: Claude Code and OpenAI Codex CLI."""

from config import ClaudeCodeConfig, CodexCliConfig


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
