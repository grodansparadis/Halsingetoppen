#!/bin/bash

# Hälsingetoppen Web Admin Startup Script

echo "Starting Hälsingetoppen Web Admin Interface..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Flask not found. Installing..."
    pip install flask
fi

# Set environment variables if needed
export FLASK_ENV=development
export FLASK_DEBUG=1

echo "Starting web server on http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application
python web_admin.py