SHELL=bash

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Archy: Intelligent Architecture Documentation CLI 🏛️"
	@echo ""
	@echo "Installation:"
	@echo "  make setup-cli        - Install 'archy' command globally (interactive)"
	@echo "  make uninstall-cli    - Remove 'archy' command from system"
	@echo ""
	@echo "CLI Tools (interactive):"
	@echo "  make create-arch      - Create architecture doc (with prompts)"
	@echo "  make update-arch      - Update architecture doc (with prompts)"
	@echo "  make fetch-pattern    - Fetch Fabric pattern (with prompts)"
	@echo "  make examples         - Show usage examples and workflows"
	@echo ""
	@echo "Usage after installation:"
	@echo "  archy --help          - Show all CLI options"
	@echo "  archy fresh           - Create fresh architecture doc"
	@echo "  archy update          - Update from git changes"

# Pure bash CLI tools - no Python setup required

.PHONY: test-scripts
test-scripts:
	@echo "Testing if required commands are available..."
	@command -v curl >/dev/null || (echo "❌ curl not found" && exit 1)
	@command -v cursor-agent >/dev/null || (echo "❌ cursor-agent not found" && exit 1) 
	@command -v jq >/dev/null || (echo "❌ jq not found" && exit 1)
	@echo "✅ All required commands available"

.PHONY: test
test: test-scripts
	@echo "✅ All tests passed!"

## CLI Tools - Interactive Architecture Generation

.PHONY: create-arch
create-arch:
	@echo "🏗️  Architecture Document Creator"
	@echo "================================="
	@echo ""
	@echo "Path options (supports absolute and relative paths):"
	@echo "  . or [Enter]              - Current directory (default)"
	@echo "  ../api                    - Relative: API service directory"
	@echo "  ../app                    - Relative: Frontend app directory"
	@echo "  /full/path/to/service     - Absolute: Any project directory"
	@echo ""
	@read -p "📁 Project path: " PROJECT_PATH; \
	PROJECT_PATH=$${PROJECT_PATH:-.}; \
	if [ ! -d "$$PROJECT_PATH" ]; then \
		echo "❌ Project path '$$PROJECT_PATH' does not exist"; \
		exit 1; \
	fi; \
	read -p "📂 Subfolder (optional, press Enter to skip): " SUBFOLDER; \
	read -p "📄 Architecture file name [arch.md]: " ARCH_FILE; \
	ARCH_FILE=$${ARCH_FILE:-arch.md}; \
	read -p "🏷️  Project name (optional, press Enter for auto-detect): " PROJECT_NAME; \
	echo ""; \
	echo "🚀 Creating architecture document..."; \
	echo "   Project: $$PROJECT_PATH"; \
	if [ -n "$$SUBFOLDER" ]; then echo "   Subfolder: $$SUBFOLDER"; fi; \
	echo "   Output: $$ARCH_FILE"; \
	if [ -n "$$PROJECT_NAME" ]; then echo "   Name: $$PROJECT_NAME"; fi; \
	echo ""; \
	if [ -n "$$SUBFOLDER" ] && [ -n "$$PROJECT_NAME" ]; then \
		./scripts/arch.sh --fresh "$$PROJECT_PATH" "$$SUBFOLDER" "$$ARCH_FILE" "$$PROJECT_NAME"; \
	elif [ -n "$$SUBFOLDER" ]; then \
		./scripts/arch.sh --fresh "$$PROJECT_PATH" "$$SUBFOLDER" "$$ARCH_FILE"; \
	elif [ -n "$$PROJECT_NAME" ]; then \
		./scripts/arch.sh --fresh "$$PROJECT_PATH" "" "$$ARCH_FILE" "$$PROJECT_NAME"; \
	else \
		./scripts/arch.sh --fresh "$$PROJECT_PATH" "" "$$ARCH_FILE"; \
	fi

.PHONY: update-arch
update-arch:
	@echo "🔄 Architecture Document Updater"
	@echo "================================"
	@echo ""
	@echo "This will analyze git changes and update existing arch.md"
	@echo ""
	@echo "Path options (supports absolute and relative paths):"
	@echo "  . or [Enter]              - Current directory (default)"
	@echo "  ../api                    - Relative: Update API service docs"  
	@echo "  ../app                    - Relative: Update frontend app docs"
	@echo "  /full/path/to/service     - Absolute: Any project directory"
	@echo ""
	@read -p "📁 Project path: " PROJECT_PATH; \
	PROJECT_PATH=$${PROJECT_PATH:-.}; \
	if [ ! -d "$$PROJECT_PATH" ]; then \
		echo "❌ Project path '$$PROJECT_PATH' does not exist"; \
		exit 1; \
	fi; \
	read -p "📂 Subfolder (optional, press Enter to skip): " SUBFOLDER; \
	read -p "📄 Architecture file name [arch.md]: " ARCH_FILE; \
	ARCH_FILE=$${ARCH_FILE:-arch.md}; \
	echo ""; \
	echo "🔍 Checking for git changes..."; \
	echo "   Project: $$PROJECT_PATH"; \
	if [ -n "$$SUBFOLDER" ]; then echo "   Subfolder: $$SUBFOLDER"; fi; \
	echo "   File: $$ARCH_FILE"; \
	echo ""; \
	if [ -n "$$SUBFOLDER" ]; then \
		./scripts/arch.sh "$$PROJECT_PATH" "$$SUBFOLDER" "$$ARCH_FILE"; \
	else \
		./scripts/arch.sh "$$PROJECT_PATH" "" "$$ARCH_FILE"; \
	fi

.PHONY: fetch-pattern
fetch-pattern:
	@echo "🔍 Fabric Pattern Fetcher"
	@echo "========================="
	@echo ""
	@echo "Fetches Fabric AI patterns from GitHub for custom prompts"
	@echo ""
	@echo "Popular patterns:"
	@echo "  create_design_document          - C4 architecture docs"
	@echo "  update_architecture_diagram     - Update existing docs" 
	@echo "  analyze_code_structure          - Code analysis"
	@echo "  create_summary                  - Project summaries"
	@echo ""
	@read -p "📋 Pattern name: " PATTERN_NAME; \
	if [ -z "$$PATTERN_NAME" ]; then \
		echo "❌ Pattern name is required"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "📥 Fetching pattern: $$PATTERN_NAME"; \
	./scripts/fetch_fabric_pattern.sh "$$PATTERN_NAME"

.PHONY: examples
examples:
	@echo "💡 Common Usage Examples"
	@echo "========================"
	@echo ""
	@echo "🏗️  Create architecture for current directory:"
	@echo "   make create-arch"
	@echo "   → Just press [Enter] for current directory"
	@echo "   → Creates arch.md with C4 diagrams"
	@echo ""
	@echo "🔄 Update docs after code changes:"
	@echo "   make update-arch  "
	@echo "   → Analyzes git diff and updates arch.md"
	@echo ""
	@echo "📋 Document multiple services (examples):"
	@echo "   cd /path/to/api && make create-arch"
	@echo "   cd /path/to/app && make create-arch"  
	@echo "   make create-arch  # Enter: ../some-service"
	@echo ""
	@echo "🎯 Pure bash CLI tools - no server needed!"
	@echo ""
	@echo "🔍 Available tools:"
	@echo "   • create_architecture  - Fresh architecture analysis (--fresh mode)"
	@echo "   • update_architecture  - Update from git changes (default mode)" 
	@echo "   • fetch_fabric_pattern - Get custom prompt patterns"
	@echo ""
	@echo "🛠️  Direct script usage:"
	@echo "   ./scripts/arch.sh --fresh [path]  - Fresh analysis mode"
	@echo "   ./scripts/arch.sh [path]          - Git changes mode (default)"

## CLI Installation

.PHONY: setup-cli
setup-cli:
	@echo "🏛️  Archy CLI Setup"
	@echo "=================="
	@echo ""
	@echo "This will install 'archy' command globally on your system."
	@echo ""
	@echo "Install locations:"
	@echo "  1) ~/.local/bin/archy        (recommended - user only)"
	@echo "  2) /usr/local/bin/archy      (system-wide, requires sudo)"
	@echo "  3) Custom location"
	@echo ""
	@read -p "Choose [1], 2, or 3: " CHOICE; \
	CHOICE=$${CHOICE:-1}; \
	case "$$CHOICE" in \
		"1") \
			INSTALL_DIR="$$HOME/.local/bin"; \
			echo "Installing to: $$INSTALL_DIR"; \
			;; \
		"2") \
			INSTALL_DIR="/usr/local/bin"; \
			echo "Installing to: $$INSTALL_DIR (will prompt for sudo)"; \
			;; \
		"3") \
			read -p "Enter custom path: " INSTALL_DIR; \
			echo "Installing to: $$INSTALL_DIR"; \
			;; \
		*) \
			echo "Invalid choice, using default: ~/.local/bin"; \
			INSTALL_DIR="$$HOME/.local/bin"; \
			;; \
	esac; \
	echo ""; \
	echo "🔧 Setting up installation..."; \
	mkdir -p "$$INSTALL_DIR" 2>/dev/null || sudo mkdir -p "$$INSTALL_DIR"; \
	chmod +x scripts/arch.sh scripts/archy; \
	if [ "$$INSTALL_DIR" = "/usr/local/bin" ]; then \
		sudo ln -sf "$(PWD)/scripts/archy" "$$INSTALL_DIR/archy"; \
	else \
		ln -sf "$(PWD)/scripts/archy" "$$INSTALL_DIR/archy"; \
	fi; \
	echo "✅ archy installed to $$INSTALL_DIR/archy"; \
	echo ""; \
	if ! echo "$$PATH" | grep -q "$$INSTALL_DIR"; then \
		echo "⚠️  Add $$INSTALL_DIR to your PATH:"; \
		if [ "$$INSTALL_DIR" = "$$HOME/.local/bin" ]; then \
			echo "  echo 'export PATH=\"\$$HOME/.local/bin:\$$PATH\"' >> ~/.zshrc"; \
		else \
			echo "  echo 'export PATH=\"$$INSTALL_DIR:\$$PATH\"' >> ~/.zshrc"; \
		fi; \
		echo "  source ~/.zshrc"; \
		echo ""; \
	fi; \
	echo "🎉 Setup complete! Usage:"; \
	echo "  archy fresh    - Create fresh architecture doc"; \
	echo "  archy update   - Update from git changes"; \
	echo "  archy          - Default: update mode"; \
	echo "  archy --help   - Show help"

.PHONY: uninstall-cli
uninstall-cli:
	@echo "🗑️  Removing archy CLI installation..."
	@echo ""
	@REMOVED=false; \
	for location in "$$HOME/.local/bin/archy" "/usr/local/bin/archy" "/usr/bin/archy"; do \
		if [ -L "$$location" ] || [ -f "$$location" ]; then \
			echo "🔍 Found: $$location"; \
			if [ "$$location" = "/usr/local/bin/archy" ] || [ "$$location" = "/usr/bin/archy" ]; then \
				echo "   Removing system installation (may need sudo)..."; \
				sudo rm -f "$$location" && echo "✅ Removed: $$location" || echo "❌ Failed to remove: $$location"; \
			else \
				rm -f "$$location" && echo "✅ Removed: $$location" || echo "❌ Failed to remove: $$location"; \
			fi; \
			REMOVED=true; \
		fi; \
	done; \
	if [ "$$REMOVED" = "false" ]; then \
		echo "ℹ️  No archy installations found in common locations:"; \
		echo "   - ~/.local/bin/archy"; \
		echo "   - /usr/local/bin/archy"; \
		echo "   - /usr/bin/archy"; \
		echo ""; \
		echo "💡 If installed elsewhere, remove manually:"; \
		echo "   which archy  # Find location"; \
		echo "   rm \$$(which archy)  # Remove it"; \
	else \
		echo ""; \
		echo "🎉 Archy CLI uninstall complete!"; \
	fi

.PHONY: clean
clean:
	rm -rf tmp/
	@echo "✅ Cleaned temporary files"

.PHONY: clean-all
clean-all: clean
	@echo "✅ Cleaned everything"