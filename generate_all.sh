#!/bin/bash

# Generate All Lists - Shell Script Wrapper
# Simplifies running the Python CLI script with proper environment

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Hälsingetoppen - Generate All Lists"
echo "===================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if database exists
if [ ! -f "toppen.sqlite3" ]; then
    echo "❌ Database file 'toppen.sqlite3' not found."
    echo "Please ensure you're in the correct directory."
    exit 1
fi

# Default options
UPDATE_SPOTIFY=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--update-spotify)
            UPDATE_SPOTIFY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -u, --update-spotify    Update artist data from Spotify first"
            echo "  -v, --verbose          Enable verbose output"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Quick generation without Spotify update"
            echo "  $0 -u                  # Full update with Spotify data"
            echo "  $0 -u -v               # Full update with verbose output"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python generate_all_cli.py"
if [ "$UPDATE_SPOTIFY" = true ]; then
    CMD="$CMD --update-spotify"
fi
if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

echo "Configuration:"
echo "  Update from Spotify: $([ "$UPDATE_SPOTIFY" = true ] && echo "Yes" || echo "No")"
echo "  Verbose output: $([ "$VERBOSE" = true ] && echo "Yes" || echo "No")"
echo ""

# Ask for confirmation if updating from Spotify
if [ "$UPDATE_SPOTIFY" = true ]; then
    echo "⚠️  Updating from Spotify will take 5-15 minutes and may trigger rate limiting."
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi
    echo ""
fi

echo "Starting generation..."
echo "Command: $CMD"
echo ""

# Run the generation
exec $CMD