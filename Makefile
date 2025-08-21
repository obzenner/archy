SHELL=bash

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Archy: 🏛️ Intelligent Architecture Documentation CLI 🏛️"
	@echo ""
	@echo "Installation:"
	@echo "  make setup-cli        - Install 'archy' command globally (interactive)"
	@echo "  make uninstall-cli    - Remove 'archy' command from system"
	@echo ""
	@echo "CLI Tools (interactive):"
	@echo "  make create-arch      - Create architecture doc (with prompts)"
	@echo "  make update-arch      - Update architecture doc (with prompts)"

	@echo "  make examples         - Show usage examples and workflows"
	@echo "  make test-ai          - Test AI backend with simple message"
	@echo ""
	@echo "Usage after installation:"
	@echo "  archy --help          - Show all CLI options"
	@echo "  archy fresh           - Create fresh architecture doc"
	@echo "  archy fresh -t fabric - Create with fabric backend"
	@echo "  archy update          - Update from git changes"
	@echo "  archy update -t fabric - Update with fabric backend"
	@echo "  archy test -t fabric  - Test fabric backend"
	@echo ""
	@echo "AI Backend Selection (use -t flag for all commands):"
	@echo "  -t cursor-agent       - Use cursor-agent backend (default)"
	@echo "  -t fabric             - Use fabric backend (supports local models)"

# Pure bash CLI tools - no Python setup required

.PHONY: test-scripts
test-scripts:
	@echo "Testing if required commands are available..."
	@command -v curl >/dev/null || (echo "ERROR: curl not found" && exit 1)
	@command -v jq >/dev/null || (echo "ERROR: jq not found" && exit 1)
	@echo "Checking AI backends..."
	@BACKEND=$${ARCHY_AI_BACKEND:-cursor-agent}; \
	if [ "$$BACKEND" = "cursor-agent" ]; then \
		command -v cursor-agent >/dev/null || (echo "ERROR: cursor-agent not found. Install from: https://cursor.com/cli" && exit 1); \
		echo "SUCCESS: cursor-agent found"; \
	elif [ "$$BACKEND" = "fabric" ]; then \
		command -v fabric-ai >/dev/null || (echo "ERROR: fabric-ai not found. Install from: https://github.com/danielmiessler/Fabric" && exit 1); \
		echo "SUCCESS: fabric-ai found"; \
	else \
		echo "ERROR: Unknown AI backend: $$BACKEND (supported: cursor-agent, fabric)"; \
		exit 1; \
	fi
	@echo "SUCCESS: All required commands available"

.PHONY: test
test: test-scripts
	@echo "SUCCESS: All tests passed!"

.PHONY: test-ai
test-ai:
	@./cli/test_ai.sh || (echo "Run 'make setup-cli' first to set up permissions" && exit 1)

## CLI Tools - Interactive Architecture Generation

.PHONY: create-arch
create-arch:
	@./cli/create_arch.sh || (echo "Run 'make setup-cli' first to set up permissions" && exit 1)

.PHONY: update-arch
update-arch:
	@./cli/update_arch.sh || (echo "Run 'make setup-cli' first to set up permissions" && exit 1)



.PHONY: examples
examples:
	@echo "Common Usage Examples"
	@echo "========================"
	@echo ""
	@echo "Basic usage (default cursor-agent backend):"
	@echo "   archy fresh                       - Create arch.md"
	@echo "   archy update                      - Update from git changes"
	@echo ""
	@echo "Using Fabric backend (with -t flag):"
	@echo "   archy fresh -t fabric             - Create with fabric"
	@echo "   archy update -t fabric            - Update with fabric"
	@echo ""
	@echo "Testing backends (with -t flag):"
	@echo "   archy test                            - Test cursor-agent (default)"
	@echo "   archy test -t fabric                  - Test fabric backend"
	@echo "   archy test -t cursor \"Custom message\" - Test with custom message"
	@echo ""
	@echo "Advanced options with backend selection:"
	@echo "   archy fresh -t fabric -f backend -d api.md      - Focus on backend/, output to api.md with fabric"
	@echo "   archy fresh -t cursor -p /path/to/repo -n MyApp  - Different project with cursor-agent"
	@echo "   archy update -t fabric -f frontend              - Update focusing on frontend/ with fabric"
	@echo "   archy update -t cursor -p ../other-repo         - Update different project with cursor-agent"
	@echo ""
	@echo "Document multiple services with different backends:"
	@echo "   cd /path/to/api && archy fresh -t cursor"
	@echo "   cd /path/to/app && archy fresh -t fabric"  
	@echo "   archy fresh -t fabric -p ../some-service"
	@echo ""
	@echo "Environment-based backend selection (alternative):"
	@echo "   export ARCHY_AI_BACKEND=fabric        - Set for session"
	@echo "   archy fresh                           - Will use fabric"
	@echo "   archy update                          - Will use fabric"
	@echo ""
	@echo "Pure bash CLI tools - no server needed!"
	@echo ""
	@echo "Available commands:"
	@echo "   • archy fresh [-t tool]   - Fresh architecture analysis (--fresh mode)"
	@echo "   • archy update [-t tool]  - Update from git changes (default mode)" 
	@echo "   • archy test [-t tool]    - Test AI backend connectivity"
	@echo ""
	@echo "Direct script usage:"
	@echo "   ARCHY_AI_BACKEND=fabric ./scripts/arch.sh --fresh [path]  - Fresh analysis with fabric"
	@echo "   ARCHY_AI_BACKEND=cursor ./scripts/arch.sh [path]          - Git changes with cursor-agent"

## CLI Installation

.PHONY: setup-cli
setup-cli:
	@chmod +x cli/setup_cli.sh && ./cli/setup_cli.sh

.PHONY: uninstall-cli
uninstall-cli:
	@./cli/uninstall_cli.sh || (echo "Run 'make setup-cli' first to set up permissions" && exit 1)

.PHONY: clean
clean:
	rm -rf tmp/
	@echo "SUCCESS: Cleaned temporary files"

.PHONY: clean-all
clean-all: clean
	@echo "SUCCESS: Cleaned everything"