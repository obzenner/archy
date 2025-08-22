SHELL=bash

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Archy: 🏛️  Intelligent Architecture Documentation CLI 🏛️"
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
	@echo "  make format-party     - 🎉 Format your code with STYLE! 🎉"
	@echo ""
	@echo "CI Testing (test locally before push):"
	@echo "  make ci-test          - Run full CI test suite (lint + type + test)"
	@echo "  make ci-full          - Run complete CI workflow (test + build + check)"
	@echo "  make build            - Build package for distribution"
	@echo "  make check-package    - Check built package integrity"
	@echo "  make test-install     - Test package installation"
	@echo "  make clean-build      - Clean all build artifacts"
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
	pytest tests/ -v --tb=short -x --timeout=30

.PHONY: test-coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	pytest tests/ -v --tb=short -x --timeout=30 --cov=src/archy --cov-report=term-missing

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

.PHONY: format-party
format-party:
	@echo "🎉 Welcome to the FORMAT PARTY! 🎉"
	@echo "🧹 Black is cleaning up the dance floor..."
	@black src/ tests/ --quiet
	@echo "✨ Ruff is adding some sparkle..."
	@ruff format src/ tests/ --quiet
	@echo "🔧 Ruff is fixing the sound system..."
	@ruff check src/ tests/ --fix --quiet || true
	@echo "🎊 FORMAT PARTY COMPLETE! Your code is looking FRESH! 🎊"
	@echo "🕺 Time to dance with your beautifully formatted code! 💃"

## CI Testing Commands (mirror GitHub Actions workflow)

.PHONY: ci-deps
ci-deps:
	@echo "📦 Installing development dependencies..."
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

.PHONY: ci-lint
ci-lint:
	@echo "🧹 Running lint checks (CI style)..."
	ruff check src/ tests/

.PHONY: ci-typecheck  
ci-typecheck:
	@echo "🎯 Running type checks (CI style)..."
	mypy src/

.PHONY: ci-test-basic
ci-test-basic:
	@echo "✅ Running basic tests (CI style)..."
	pytest tests/ -v --tb=short -x --timeout=30

.PHONY: ci-test-coverage
ci-test-coverage:
	@echo "📊 Running tests with coverage (CI style)..."
	pytest tests/ -v --tb=short -x --timeout=30 --cov=src/archy --cov-report=xml --cov-report=term

.PHONY: ci-test
ci-test: ci-deps ci-lint ci-typecheck ci-test-basic
	@echo "✅ All CI test steps completed successfully!"

.PHONY: build
build:
	@echo "🔨 Building package..."
	python -m pip install --upgrade pip build
	python -m build
	@echo "✅ Package built successfully!"

.PHONY: check-package
check-package: build
	@echo "🔍 Checking package integrity..."
	python -m pip install --upgrade twine
	twine check dist/*
	@echo "✅ Package check completed!"

.PHONY: test-install
test-install: build
	@echo "🧪 Testing package installation..."
	@# Create temporary virtual environment for clean test
	python -m venv /tmp/archy-test-env
	source /tmp/archy-test-env/bin/activate && \
		pip install --upgrade pip && \
		pip install dist/*.whl && \
		archy --help && \
		echo "✅ Package installation test successful!"
	rm -rf /tmp/archy-test-env

.PHONY: ci-full
ci-full: ci-test build check-package test-install
	@echo "🎉 Complete CI workflow successful! Ready to push/release."

.PHONY: clean-build
clean-build:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true











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
	@echo "Modern Python CLI - clean and reliable!"
	@echo ""
	@echo "Available commands:"
	@echo "   • archy fresh [-t tool]   - Fresh architecture analysis"
	@echo "   • archy update [-t tool]  - Update from git changes" 
	@echo "   • archy test [-t tool]    - Test AI backend connectivity"
	@echo "   • archy version           - Show version information"



# Legacy clean targets (use clean-build instead)
.PHONY: clean
clean: clean-build
	@echo "✅ Cleaned temporary files (redirected to clean-build)"

.PHONY: clean-all
clean-all: clean-build
	@echo "✅ Cleaned everything (redirected to clean-build)"