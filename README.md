# Archy 🏛️

[![CI Tests](https://github.com/obzenner/archy/actions/workflows/ci.yml/badge.svg)](https://github.com/obzenner/archy/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/archy.svg)](https://badge.fury.io/py/archy)
[![Python versions](https://img.shields.io/pypi/pyversions/archy.svg)](https://pypi.org/project/archy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Intelligent Architecture Documentation CLI** - Generate C4 architecture diagrams and documentation from your codebase using AI.

Archy analyzes your git repository and automatically creates comprehensive architecture documentation with Context, Container, and Deployment diagrams using the C4 model.

## 🚀 Installation

```bash
pip install archy
```

## 📋 Requirements

You'll need one of these AI backends:

- **[Cursor Agent CLI](https://cursor.com/cli)** - Official Cursor AI CLI tool  
- **[Fabric](https://github.com/danielmiessler/Fabric)** - Open-source AI framework (great for local models)

## 🎯 Quick Start

```bash
# Generate fresh architecture documentation
archy fresh /path/to/your/project

# Update existing documentation based on git changes  
archy update /path/to/your/project

# Test your AI backend connection
archy test --tool cursor-agent
archy test --tool fabric

# Get help
archy --help
```

## ✨ Features

- 🏗️ **Automatic codebase analysis** - Scans your entire project structure
- 🎨 **C4 model diagrams** - Generates Context, Container, and Deployment views
- 🔄 **Git-aware updates** - Intelligent updates based on code changes
- 🎛️ **Multiple AI backends** - Works with Cursor Agent or Fabric
- 🎯 **Project-specific insights** - Uses real service names, not generic placeholders
- 🌈 **Beautiful CLI** - Rich terminal output with progress indicators

## 📖 Documentation

For detailed usage instructions and examples:

```bash
make help  # If you're in a development environment
```

Or visit our [documentation](https://github.com/obzenner/archy) for more information.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For development, all CI steps can be run locally using make targets:

```bash
make ci-test     # Run the same tests as CI
make ci-full     # Run complete CI workflow (test + build + check)
```

This ensures consistency between your local development environment and CI.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
