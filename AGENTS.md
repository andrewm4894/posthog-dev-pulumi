# Repository Guidelines

## Project Structure & Module Organization
- `__main__.py` is the Pulumi entry point; it wires config, networking, and VM creation.
- `config.py`, `network.py`, `vm.py`, and `constants.py` hold the core infra logic.
- `startup_scripts/` assembles the VM provisioning bash script (see `full_startup.py` and `sections/`).
- `vms.yaml` is the recommended place for VM definitions and defaults (no secrets).
- `Pulumi.yaml` and `Pulumi.dev.yaml` define Pulumi project metadata and stack defaults.

## Build, Test, and Development Commands
- `uv sync` installs Python dependencies for this Pulumi app.
- `pulumi preview` shows infra changes before apply.
- `pulumi up` deploys or updates the GCP resources.
- `pulumi destroy` tears down all managed resources for the selected stack.
- `make new-vm NAME=my-feature PROJECT=my-gcp-project [BRANCH=feature-branch]` creates a new stack.
- `make ssh VM=posthog-dev-1` uses IAP tunneling to connect to a VM.
- `make logs VM=posthog-dev-1` tails startup logs from the VM.

## Coding Style & Naming Conventions
- Python 3.11+; keep modules small and focused by responsibility.
- Use `snake_case` for functions/variables and `PascalCase` for classes (dataclasses in `config.py`).
- VM names follow `posthog-<name>`; prefer matching entries in `vms.yaml`.
- No formatter or linter is configured here—keep changes clean and readable.

## Testing Guidelines
- There is no automated test suite in this repo.
- Validate changes by running `pulumi preview` and reviewing the plan output.

## Commit & Pull Request Guidelines
- Commit messages are short, imperative, and specific (e.g., “Fix Claude Code install…”).
- PRs should include: a brief summary, the affected stack(s), and a `pulumi preview` snippet.
- Link related issues or tickets when applicable; call out any secrets/config changes explicitly.

## Security & Configuration Tips
- Store secrets in Google Secret Manager and reference names via Pulumi config or `vms.yaml`.
- Never commit API keys or passwords to `vms.yaml` or source files.
- VMs have no external IPs; access is via IAP SSH or Chrome Remote Desktop.
