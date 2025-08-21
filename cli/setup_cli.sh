#!/bin/bash

# Interactive CLI setup script - Install 'archy' command globally
# Called by: make setup-cli

set -euo pipefail

#================================================================
# CONFIGURATION
#================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly CLI_COMMAND_NAME="archy"
readonly DEFAULT_CHOICE="1"

# Supported installation locations
readonly USER_LOCAL_BIN="$HOME/.local/bin"
readonly SYSTEM_BIN="/usr/local/bin"

# Installation choice options
readonly CHOICE_USER_LOCAL="1"
readonly CHOICE_SYSTEM_WIDE="2" 
readonly CHOICE_CUSTOM="3"

#================================================================
# GLOBAL VARIABLES
#================================================================
# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Installation parameters (set during execution)
CHOSEN_INSTALL_DIR=""
PROJECT_ROOT_DIR=""

#================================================================
# UTILITY FUNCTIONS
#================================================================

# Print error message and exit
error_exit() {
    local message="$1"
    local exit_code="${2:-1}"
    
    echo -e "${RED}ERROR: $message${NC}" >&2
    exit "$exit_code"
}

# Print informational message
info() {
    local message="$1"
    echo -e "${CYAN}$message${NC}"
}

# Print success message
success() {
    local message="$1"
    echo -e "${GREEN}$message${NC}"
}

# Print warning message
warn() {
    local message="$1"
    echo -e "${YELLOW}$message${NC}"
}

#================================================================
# INSTALLATION SETUP FUNCTIONS
#================================================================

# Display installation header and options
show_installation_options() {
    info "Archy CLI Setup"
    echo "=================="
    echo ""
    echo "This will install '$CLI_COMMAND_NAME' command globally on your system."
    echo ""
    echo "Install locations:"
    echo "  $CHOICE_USER_LOCAL) $USER_LOCAL_BIN/$CLI_COMMAND_NAME        (recommended - user only)"
    echo "  $CHOICE_SYSTEM_WIDE) $SYSTEM_BIN/$CLI_COMMAND_NAME      (system-wide, requires sudo)"
    echo "  $CHOICE_CUSTOM) Custom location"
    echo ""
}

# Get user's installation choice
get_installation_choice() {
    local user_choice
    read -p "Choose [$DEFAULT_CHOICE], $CHOICE_SYSTEM_WIDE, or $CHOICE_CUSTOM: " user_choice
    user_choice=${user_choice:-$DEFAULT_CHOICE}
    
    case "$user_choice" in
        "$CHOICE_USER_LOCAL")
            CHOSEN_INSTALL_DIR="$USER_LOCAL_BIN"
            echo "Installing to: $CHOSEN_INSTALL_DIR"
            ;;
        "$CHOICE_SYSTEM_WIDE")
            CHOSEN_INSTALL_DIR="$SYSTEM_BIN"
            echo "Installing to: $CHOSEN_INSTALL_DIR (will prompt for sudo)"
            ;;
        "$CHOICE_CUSTOM")
            read -p "Enter custom path: " CHOSEN_INSTALL_DIR
            echo "Installing to: $CHOSEN_INSTALL_DIR"
            ;;
        *)
            warn "Invalid choice, using default: $USER_LOCAL_BIN"
            CHOSEN_INSTALL_DIR="$USER_LOCAL_BIN"
            ;;
    esac
}

# Set up project environment and permissions
setup_project_environment() {
    # Get the project root directory (assuming this script is in cli/)
    PROJECT_ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
    
    info "Setting up installation..."
    echo "Setting executable permissions on scripts..."
    
    # Set executable permissions on all necessary scripts
    chmod +x "$PROJECT_ROOT_DIR/scripts/"*.sh \
             "$PROJECT_ROOT_DIR/scripts/$CLI_COMMAND_NAME" \
             "$PROJECT_ROOT_DIR/cli/"*.sh
}

# Create installation directory with appropriate permissions
create_install_directory() {
    # Try to create directory normally first, then with sudo if needed
    if ! mkdir -p "$CHOSEN_INSTALL_DIR" 2>/dev/null; then
        info "Creating directory requires elevated permissions..."
        sudo mkdir -p "$CHOSEN_INSTALL_DIR" || error_exit "Failed to create installation directory: $CHOSEN_INSTALL_DIR"
    fi
}

# Install the CLI command by creating symlink
install_cli_command() {
    local source_path="$PROJECT_ROOT_DIR/scripts/$CLI_COMMAND_NAME"
    local target_path="$CHOSEN_INSTALL_DIR/$CLI_COMMAND_NAME"
    
    # Use sudo for system-wide installation
    if [[ "$CHOSEN_INSTALL_DIR" == "$SYSTEM_BIN" ]]; then
        sudo ln -sf "$source_path" "$target_path" || error_exit "Failed to create symlink with sudo"
    else
        ln -sf "$source_path" "$target_path" || error_exit "Failed to create symlink"
    fi
    
    success "$CLI_COMMAND_NAME installed to $target_path"
}

# Check if installation directory is in PATH and provide guidance
check_path_configuration() {
    echo ""
    
    if ! echo "$PATH" | grep -q "$CHOSEN_INSTALL_DIR"; then
        warn "Add $CHOSEN_INSTALL_DIR to your PATH:"
        
        if [[ "$CHOSEN_INSTALL_DIR" == "$USER_LOCAL_BIN" ]]; then
            echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
        else
            echo "  echo 'export PATH=\"$CHOSEN_INSTALL_DIR:\$PATH\"' >> ~/.zshrc"
        fi
        echo "  source ~/.zshrc"
        echo ""
    fi
}

# Display installation success message and usage
show_completion_message() {
    success "Setup complete! Usage:"
    echo "  $CLI_COMMAND_NAME fresh    - Create fresh architecture doc"
    echo "  $CLI_COMMAND_NAME update   - Update from git changes"
    echo "  $CLI_COMMAND_NAME          - Default: update mode"
    echo "  $CLI_COMMAND_NAME --help   - Show help"
}

#================================================================
# MAIN EXECUTION FUNCTION
#================================================================

# Main installation orchestration function
main() {
    show_installation_options
    get_installation_choice
    setup_project_environment
    create_install_directory
    install_cli_command
    check_path_configuration
    show_completion_message
}

#================================================================
# SCRIPT ENTRY POINT
#================================================================

# Execute main installation process
main "$@"
