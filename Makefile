# PostHog Dev VMs - Makefile
# Common commands for managing PostHog development VMs on GCP

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

##@ Setup

.PHONY: install
install: ## Install Python dependencies with uv
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv sync

.PHONY: auth
auth: ## Authenticate with GCP (required before first deploy)
	@echo "$(BLUE)Setting up GCP authentication...$(NC)"
	gcloud auth application-default login

##@ Deployment

.PHONY: preview
preview: ## Preview infrastructure changes
	@echo "$(BLUE)Previewing changes...$(NC)"
	pulumi preview

.PHONY: up
up: ## Deploy/update infrastructure
	@echo "$(BLUE)Deploying infrastructure...$(NC)"
	pulumi up

.PHONY: destroy
destroy: ## Destroy all infrastructure
	@echo "$(YELLOW)WARNING: This will destroy all VMs!$(NC)"
	pulumi destroy

.PHONY: refresh
refresh: ## Refresh state from cloud
	@echo "$(BLUE)Refreshing state...$(NC)"
	pulumi refresh

##@ Configuration

.PHONY: config
config: ## Show current configuration
	@echo "$(BLUE)Current configuration:$(NC)"
	pulumi config

.PHONY: outputs
outputs: ## Show stack outputs (IPs, SSH commands, etc.)
	@echo "$(BLUE)Stack outputs:$(NC)"
	pulumi stack output

.PHONY: set-ip
set-ip: ## Update allowed IPs (usage: make set-ip IP=1.2.3.4)
	@if [ -z "$(IP)" ]; then \
		echo "$(YELLOW)Usage: make set-ip IP=YOUR.IP.HERE$(NC)"; \
		echo "Find your IP at: https://whatismyip.com"; \
	else \
		echo "$(BLUE)Setting allowed IP to $(IP)/32...$(NC)"; \
		pulumi config set allowedIps '["$(IP)/32"]'; \
		echo "$(GREEN)Done! Run 'make up' to apply changes.$(NC)"; \
	fi

.PHONY: set-branch
set-branch: ## Set PostHog branch (usage: make set-branch BRANCH=my-feature)
	@if [ -z "$(BRANCH)" ]; then \
		echo "$(YELLOW)Usage: make set-branch BRANCH=branch-name$(NC)"; \
	else \
		echo "$(BLUE)Setting PostHog branch to $(BRANCH)...$(NC)"; \
		pulumi config set posthogBranch $(BRANCH); \
		echo "$(GREEN)Done! Run 'make up' to apply changes.$(NC)"; \
	fi

##@ VM Management

.PHONY: ssh
ssh: ## SSH into default VM (usage: make ssh or make ssh VM=vm-name)
	@VM_NAME=$${VM:-posthog-dev-1}; \
	ZONE=$$(pulumi config get gcp:zone 2>/dev/null || echo "europe-west1-b"); \
	PROJECT=$$(pulumi config get gcp:project); \
	echo "$(BLUE)SSHing into $$VM_NAME...$(NC)"; \
	gcloud compute ssh $$VM_NAME --zone=$$ZONE --project=$$PROJECT

.PHONY: start-vm
start-vm: ## Start a stopped VM (usage: make start-vm VM=vm-name)
	@VM_NAME=$${VM:-posthog-dev-1}; \
	ZONE=$$(pulumi config get gcp:zone 2>/dev/null || echo "europe-west1-b"); \
	PROJECT=$$(pulumi config get gcp:project); \
	echo "$(BLUE)Starting $$VM_NAME...$(NC)"; \
	gcloud compute instances start $$VM_NAME --zone=$$ZONE --project=$$PROJECT

.PHONY: stop-vm
stop-vm: ## Stop a running VM to save costs (usage: make stop-vm VM=vm-name)
	@VM_NAME=$${VM:-posthog-dev-1}; \
	ZONE=$$(pulumi config get gcp:zone 2>/dev/null || echo "europe-west1-b"); \
	PROJECT=$$(pulumi config get gcp:project); \
	echo "$(YELLOW)Stopping $$VM_NAME...$(NC)"; \
	gcloud compute instances stop $$VM_NAME --zone=$$ZONE --project=$$PROJECT

.PHONY: list-vms
list-vms: ## List all PostHog dev VMs
	@PROJECT=$$(pulumi config get gcp:project); \
	echo "$(BLUE)PostHog dev VMs in project $$PROJECT:$(NC)"; \
	gcloud compute instances list --filter="labels.purpose=posthog-dev" --project=$$PROJECT

.PHONY: logs
logs: ## View startup script logs (usage: make logs VM=vm-name)
	@VM_NAME=$${VM:-posthog-dev-1}; \
	ZONE=$$(pulumi config get gcp:zone 2>/dev/null || echo "europe-west1-b"); \
	PROJECT=$$(pulumi config get gcp:project); \
	echo "$(BLUE)Fetching logs from $$VM_NAME...$(NC)"; \
	gcloud compute ssh $$VM_NAME --zone=$$ZONE --project=$$PROJECT --command="sudo cat /var/log/posthog-startup.log"

##@ Help

.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)PostHog Dev VMs - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Examples:$(NC)"
	@echo "  make install          # Install dependencies"
	@echo "  make auth             # Authenticate with GCP"
	@echo "  make up               # Deploy VMs"
	@echo "  make ssh              # SSH into default VM"
	@echo "  make set-ip IP=1.2.3.4  # Update allowed IP"
	@echo "  make stop-vm          # Stop VM to save costs"
