SHELL=bash

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Archy: 🏛️ Intelligent Architecture Documentation CLI 🏛️"
	@echo ""
	@echo "Python Installation (Recommended):"
	@echo "  make install          - Install archy CLI in development mode"
	@echo "  make install-user     - Install archy CLI for current user only"
	@echo "  make install-dev      - Install in development mode with testing tools"
	@echo "  make uninstall        - Remove archy CLI from system"
	@echo ""
	@echo "Development:"
	@echo "  make test             - Run all tests"
	@echo "  make lint             - Run code linting and formatting"
	@echo "  make format           - Format code with black and ruff"
	@echo ""
	@echo "Legacy Bash CLI (Deprecated):"
	@echo "  make setup-cli-bash   - Install bash version (legacy compatibility)"
	@echo "  make test-ai-bash     - Test AI backend with bash scripts"
	@echo ""
	@echo "Usage after installation:"
	@echo "  archy --help          - Show all CLI options"
	@echo "  archy fresh           - Create fresh architecture doc"
	@echo "  archy fresh -t fabric - Create with fabric backend"
	@echo "  archy update          - Update from git changes"
	@echo "  archy update -t fabric - Update with fabric backend"
	@echo "  archy test -t fabric  - Test fabric backend"
	@echo "  archy version         - Show version information"
	@echo ""
	@echo "AI Backend Selection (use -t flag for all commands):"
	@echo "  -t cursor-agent       - Use cursor-agent backend (default)"
	@echo "  -t fabric             - Use fabric backend (supports local models)"

## Python Installation Commands

.PHONY: install
install:
	@echo "🏛️ Installing Archy in development mode..."
	pip install -e .
	@echo "✅ Installation complete! Run 'archy --help' to get started."

.PHONY: install-user  
install-user:
	@echo "🏛️ Installing Archy for current user..."
	pip install --user .
	@echo "✅ Installation complete! Run 'archy --help' to get started."
	@echo "💡 Make sure ~/.local/bin is in your PATH"

.PHONY: install-dev
install-dev:
	@echo "🏛️ Installing Archy in development mode with dev dependencies..."
	pip install -e ".[dev]"
	@echo "✅ Development installation complete!"

.PHONY: uninstall
uninstall:
	@echo "🗑️ Uninstalling Archy..."
	pip uninstall -y archy || echo "Archy not installed via pip"
	@echo "✅ Uninstall complete!"

## Development Commands

.PHONY: test
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

.PHONY: test-coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ --cov=src/archy --cov-report=term-missing

.PHONY: lint
lint:
	@echo "🔍 Running linting..."
	ruff check src/ tests/
	mypy src/

.PHONY: format
format:
	@echo "✨ Formatting code..."
	black src/ tests/
	ruff format src/ tests/

.PHONY: format-check
format-check:
	@echo "🔍 Checking code formatting..."
	black --check src/ tests/
	ruff format --check src/ tests/

## Legacy Bash CLI Commands (Deprecated)

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

.PHONY: test-scripts-bash
test-scripts-bash:
	@echo "SUCCESS: All bash script tests passed!"

.PHONY: test-ai-bash
test-ai-bash:
	@./cli/test_ai.sh || (echo "Run 'make setup-cli-bash' first to set up permissions" && exit 1)

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

## Legacy Bash CLI Installation (Deprecated)

.PHONY: setup-cli-bash
setup-cli-bash:
	@echo "⚠️ WARNING: Installing legacy bash CLI. Consider using 'make install' instead."
	@chmod +x cli/setup_cli.sh && ./cli/setup_cli.sh

.PHONY: uninstall-cli-bash
uninstall-cli-bash:
	@./cli/uninstall_cli.sh || (echo "Run 'make setup-cli-bash' first to set up permissions" && exit 1)

.PHONY: clean
clean:
	rm -rf tmp/
	@echo "SUCCESS: Cleaned temporary files"

.PHONY: clean-all
clean-all: clean
	@echo "SUCCESS: Cleaned everything"