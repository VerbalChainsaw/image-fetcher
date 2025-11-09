#!/bin/bash

###############################################################################
# Video Fetcher Pro - Auto Setup Script
#
# One-command installation and configuration
# Usage: ./setup.sh [--full]
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji support
CHECKMARK="✓"
CROSS="✗"
ROCKET="🚀"
GEAR="⚙️"
PACKAGE="📦"
DATABASE="💾"
WEB="🌐"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}${GEAR} $1${NC}"
}

print_success() {
    echo -e "${GREEN}${CHECKMARK} $1${NC}"
}

print_error() {
    echo -e "${RED}${CROSS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# Detection Functions
###############################################################################

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python 3.8+ required (found $PYTHON_VERSION)"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

check_pip() {
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
        return 0
    else
        print_error "pip3 not found"
        return 1
    fi
}

check_ffmpeg() {
    if command -v ffmpeg &> /dev/null; then
        FFMPEG_VERSION=$(ffmpeg -version | head -1 | cut -d' ' -f3)
        print_success "FFmpeg $FFMPEG_VERSION found"
        return 0
    else
        print_warning "FFmpeg not found (optional, for video validation)"
        return 1
    fi
}

check_ffprobe() {
    if command -v ffprobe &> /dev/null; then
        print_success "FFprobe found"
        return 0
    else
        print_warning "FFprobe not found (optional, for video validation)"
        return 1
    fi
}

###############################################################################
# Installation Functions
###############################################################################

install_dependencies() {
    print_step "Installing Python dependencies..."

    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt --quiet --upgrade
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        return 1
    fi
}

install_ffmpeg() {
    print_step "Installing FFmpeg..."

    OS=$(detect_os)

    case $OS in
        linux)
            if command -v apt-get &> /dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y ffmpeg
            elif command -v yum &> /dev/null; then
                sudo yum install -y ffmpeg
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm ffmpeg
            else
                print_warning "Could not detect package manager. Please install FFmpeg manually."
                return 1
            fi
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install ffmpeg
            else
                print_warning "Homebrew not found. Please install FFmpeg manually."
                return 1
            fi
            ;;
        *)
            print_warning "Automatic FFmpeg installation not supported on this OS."
            return 1
            ;;
    esac

    print_success "FFmpeg installed"
}

create_directories() {
    print_step "Creating directories..."

    mkdir -p video_collections
    mkdir -p logs
    mkdir -p cache

    print_success "Directories created"
}

setup_configuration() {
    print_step "Setting up configuration..."

    CONFIG_FILE="$HOME/.video_fetcher_config.json"

    if [ -f "$CONFIG_FILE" ]; then
        print_info "Configuration already exists at $CONFIG_FILE"
        read -p "Overwrite? (y/N): " OVERWRITE
        if [[ ! $OVERWRITE =~ ^[Yy]$ ]]; then
            print_info "Keeping existing configuration"
            return 0
        fi
    fi

    # Interactive configuration
    echo ""
    echo -e "${CYAN}API Key Configuration${NC}"
    echo -e "${BLUE}You can get free API keys from:${NC}"
    echo "  • Pexels: https://www.pexels.com/api/"
    echo "  • Pixabay: https://pixabay.com/api/docs/"
    echo ""

    read -p "Enter Pexels API key (or press Enter to skip): " PEXELS_KEY
    read -p "Enter Pixabay API key (or press Enter to skip): " PIXABAY_KEY

    # Create config file
    cat > "$CONFIG_FILE" <<EOF
{
  "pexels_api_key": "${PEXELS_KEY}",
  "pixabay_api_key": "${PIXABAY_KEY}",
  "default_source": "all",
  "default_quality": "hd",
  "default_orientation": null,
  "default_category": null,
  "output_dir": "video_collections",
  "min_duration": null,
  "max_duration": null,
  "min_width": 1280,
  "min_height": 720,
  "max_file_size_mb": 100,
  "parallel_downloads": 3,
  "theme": "dark"
}
EOF

    print_success "Configuration saved to $CONFIG_FILE"
}

make_executable() {
    print_step "Making scripts executable..."

    chmod +x video_fetcher.py 2>/dev/null || true
    chmod +x video_fetcher_pro.py 2>/dev/null || true
    chmod +x video_web_app.py 2>/dev/null || true
    chmod +x video_web_app_pro.py 2>/dev/null || true
    chmod +x setup.sh 2>/dev/null || true

    print_success "Scripts are executable"
}

run_tests() {
    print_step "Running tests..."

    # Test database
    python3 -c "
from video_database import VideoDatabase
db = VideoDatabase('/tmp/test_setup.db')
print('✓ Database OK')
" || { print_error "Database test failed"; return 1; }

    # Test config
    python3 -c "
from video_config import VideoConfig
config = VideoConfig.load_config()
print('✓ Config OK')
" || { print_error "Config test failed"; return 1; }

    # Test async sources
    python3 -c "
from video_sources_async import CircuitBreaker
cb = CircuitBreaker()
print('✓ Async sources OK')
" || { print_error "Async sources test failed"; return 1; }

    print_success "All tests passed"
}

create_systemd_service() {
    print_step "Creating systemd service (optional)..."

    read -p "Create systemd service for auto-start? (y/N): " CREATE_SERVICE
    if [[ ! $CREATE_SERVICE =~ ^[Yy]$ ]]; then
        return 0
    fi

    SERVICE_FILE="/etc/systemd/system/video-fetcher.service"
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)

    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Video Fetcher Pro Web Application
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$(which python3) $CURRENT_DIR/video_web_app_pro.py --host 0.0.0.0 --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable video-fetcher.service

    print_success "Systemd service created and enabled"
    print_info "Start with: sudo systemctl start video-fetcher"
}

###############################################################################
# Main Setup
###############################################################################

main() {
    clear
    print_header "${ROCKET} Video Fetcher Pro - Auto Setup"

    echo -e "${CYAN}This script will set up Video Fetcher Pro on your system.${NC}"
    echo ""

    FULL_INSTALL=false
    if [ "$1" == "--full" ]; then
        FULL_INSTALL=true
        print_info "Full installation mode enabled"
    fi

    # Detect OS
    OS=$(detect_os)
    print_info "Detected OS: $OS"
    echo ""

    # Check prerequisites
    print_header "${PACKAGE} Checking Prerequisites"

    check_python || exit 1
    check_pip || exit 1

    HAS_FFMPEG=false
    check_ffmpeg && HAS_FFMPEG=true
    check_ffprobe

    echo ""

    # Install FFmpeg if requested
    if [ "$FULL_INSTALL" = true ] && [ "$HAS_FFMPEG" = false ]; then
        print_header "${PACKAGE} Installing FFmpeg"
        install_ffmpeg || print_warning "FFmpeg installation failed, continuing anyway"
        echo ""
    fi

    # Install dependencies
    print_header "${PACKAGE} Installing Dependencies"
    install_dependencies || exit 1
    echo ""

    # Create directories
    print_header "${DATABASE} Setting Up Directories"
    create_directories || exit 1
    echo ""

    # Setup configuration
    print_header "${GEAR} Configuration"
    setup_configuration || exit 1
    echo ""

    # Make scripts executable
    print_header "${GEAR} Finalizing Installation"
    make_executable || exit 1
    echo ""

    # Run tests
    print_header "${GEAR} Running Tests"
    run_tests || print_warning "Some tests failed, but installation continued"
    echo ""

    # Create systemd service if on Linux
    if [ "$OS" = "linux" ] && [ "$FULL_INSTALL" = true ]; then
        print_header "${GEAR} System Integration"
        create_systemd_service
        echo ""
    fi

    # Success!
    print_header "${ROCKET} Installation Complete!"

    echo -e "${GREEN}Video Fetcher Pro is now installed and ready to use!${NC}"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo ""
    echo -e "  ${YELLOW}CLI (Basic):${NC}"
    echo "    python3 video_fetcher.py \"ocean waves\" 10"
    echo ""
    echo -e "  ${YELLOW}CLI (Pro - Async):${NC}"
    echo "    python3 video_fetcher_pro.py \"nature\" 20 --quality hd"
    echo ""
    echo -e "  ${YELLOW}Web Interface:${NC}"
    echo "    python3 video_web_app_pro.py"
    echo "    Then open: http://localhost:5001"
    echo ""
    echo -e "  ${YELLOW}Interactive Setup:${NC}"
    echo "    python3 video_fetcher_pro.py --setup"
    echo ""
    echo -e "${CYAN}Documentation:${NC}"
    echo "  • Basic Guide: VIDEO_README.md"
    echo "  • Pro Guide: VIDEO_PRO_README.md"
    echo ""

    if [ "$OS" = "linux" ] && [ "$FULL_INSTALL" = true ]; then
        echo -e "${CYAN}Service Management:${NC}"
        echo "  • Start: sudo systemctl start video-fetcher"
        echo "  • Stop: sudo systemctl stop video-fetcher"
        echo "  • Status: sudo systemctl status video-fetcher"
        echo ""
    fi

    print_success "Setup complete! Happy video collecting! ${ROCKET}"
    echo ""
}

###############################################################################
# Run
###############################################################################

# Check if script is run directly
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    main "$@"
fi
