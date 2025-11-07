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

# Check if port 5000 is available, if not try 5001
PORT=5000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "Port $PORT is already in use, trying port 5001..."
    PORT=5001
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $PORT is also in use. Please stop other Flask applications or specify a different port."
        echo "You can manually start with: python web_admin.py"
        exit 1
    fi
fi

# Set environment variables if needed
export FLASK_ENV=development
export FLASK_DEBUG=1

echo "Starting web server on http://localhost:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the application with specified port
if [ "$PORT" = "5001" ]; then
    python -c "
import web_admin
web_admin.app.run(debug=True, host='0.0.0.0', port=5001)
"
else
    # Default port 5000
    python web_admin.py
fi