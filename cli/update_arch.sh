#!/bin/bash

# Interactive architecture document updater
# Called by: make update-arch

set -euo pipefail

#================================================================
# CONFIGURATION
#================================================================
readonly SCRIPT_NAME="$(basename "$0")"
readonly DEFAULT_PROJECT_PATH="."
readonly DEFAULT_ARCH_FILENAME="arch.md"

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

# User input parameters (set during execution)
PROJECT_PATH=""
SUBFOLDER=""
ARCH_FILENAME=""
ARCH_SCRIPT_PATH=""

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
# INPUT COLLECTION FUNCTIONS
#================================================================

# Display header and information about the update process
show_update_options() {
    info "Architecture Document Updater"
    echo "================================"
    echo ""
    echo "This will analyze git changes and update existing $DEFAULT_ARCH_FILENAME"
    echo ""
    echo "Path options (supports absolute and relative paths):"
    echo "  . or [Enter]              - Current directory (default)"
    echo "  ../api                    - Relative: Update API service docs"  
    echo "  ../app                    - Relative: Update frontend app docs"
    echo "  /full/path/to/service     - Absolute: Any project directory"
    echo ""
}

# Get project path from user and validate it exists
get_project_path() {
    read -p "Project path: " PROJECT_PATH
    PROJECT_PATH=${PROJECT_PATH:-$DEFAULT_PROJECT_PATH}
    
    if [[ ! -d "$PROJECT_PATH" ]]; then
        error_exit "Project path '$PROJECT_PATH' does not exist"
    fi
}

# Get optional configuration from user
get_optional_parameters() {
    read -p "Subfolder (optional, press Enter to skip): " SUBFOLDER
    read -p "Architecture file name [$DEFAULT_ARCH_FILENAME]: " ARCH_FILENAME
    ARCH_FILENAME=${ARCH_FILENAME:-$DEFAULT_ARCH_FILENAME}
}

#================================================================
# EXECUTION FUNCTIONS
#================================================================

# Display the configuration summary to user
show_execution_summary() {
    echo ""
    warn "Checking for git changes..."
    echo "   Project: $PROJECT_PATH"
    
    if [[ -n "$SUBFOLDER" ]]; then 
        echo "   Subfolder: $SUBFOLDER"
    fi
    
    echo "   File: $ARCH_FILENAME"
    echo ""
}

# Find and validate the arch.sh script location
find_arch_script() {
    # Find the scripts directory (assuming this script is in cli/ and scripts/ is at same level)
    local scripts_dir
    scripts_dir="$(cd "$(dirname "$0")/../scripts" && pwd)"
    ARCH_SCRIPT_PATH="$scripts_dir/arch.sh"
    
    if [[ ! -f "$ARCH_SCRIPT_PATH" ]]; then
        error_exit "Cannot find arch.sh script at: $ARCH_SCRIPT_PATH"
    fi
}

# Build and execute the architecture update command
execute_architecture_update() {
    # Build command arguments - update mode doesn't use --fresh flag
    local cmd_args=("$ARCH_SCRIPT_PATH" "$PROJECT_PATH")
    
    # Add subfolder (empty string if not provided)
    cmd_args+=("${SUBFOLDER:-}")
    
    # Add architecture filename
    cmd_args+=("$ARCH_FILENAME")
    
    # Execute the architecture update command
    exec "${cmd_args[@]}"
}

#================================================================
# MAIN EXECUTION FUNCTION
#================================================================

# Main orchestration function
main() {
    show_update_options
    get_project_path
    get_optional_parameters
    show_execution_summary
    find_arch_script
    execute_architecture_update
}

#================================================================
# SCRIPT ENTRY POINT
#================================================================

# Execute main function
main "$@"
