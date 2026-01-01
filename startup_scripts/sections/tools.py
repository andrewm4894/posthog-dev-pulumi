"""Developer tools: Claude Code and OpenAI Codex CLI."""

from config import ClaudeCodeConfig, CodexCliConfig


def get_claude_code_install(claude_code: ClaudeCodeConfig) -> str:
    """Generate Claude Code binary installation section (run before user creation)."""
    if not claude_code.enabled or not claude_code.api_key:
        return ""

    return '''
section_start "Claude Code Install"
curl -fsSL https://claude.ai/install.sh | bash
section_end "Claude Code Install"
'''


def get_claude_code_config(claude_code: ClaudeCodeConfig) -> str:
    """Generate Claude Code user configuration section (run after user creation)."""
    if not claude_code.enabled or not claude_code.api_key:
        return ""

    return f'''
section_start "Claude Code Config"

# Create Claude Code configuration directory for ph user
mkdir -p /home/ph/.claude

# Create settings.json with API key and permissions for headless use
cat > /home/ph/.claude/settings.json << 'CLAUDEEOF'
{{
  "permissions": {{
    "allow": ["Bash", "Read", "Edit", "Write", "Glob", "Grep", "WebFetch"]
  }}
}}
CLAUDEEOF

# Set environment variable for API key in user's profile
cat >> /home/ph/.bashrc << 'CLAUDEENVEOF'

# Claude Code configuration
export ANTHROPIC_API_KEY="{claude_code.api_key}"
export PATH="$HOME/.local/bin:$PATH"
alias claude='~/.local/bin/claude'
CLAUDEENVEOF

chown -R ph:ph /home/ph/.claude
section_end "Claude Code Config"
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
