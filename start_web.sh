#!/bin/bash
#
# Image Fetcher Web Interface Launcher
# Starts the beautiful web interface on http://127.0.0.1:5000
#

echo "================================================================"
echo "           🎨 Image Fetcher Pro - Web Interface"
echo "================================================================"
echo ""
echo "Starting web server..."
echo ""

# Check if dependencies are installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Flask not installed. Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the web server
echo "✓ Web server starting on: http://127.0.0.1:5000"
echo ""
echo "Features:"
echo "  🎨 Beautiful modern UI"
echo "  📊 Real-time progress tracking"
echo "  🖼️  Image gallery & preview"
echo "  📚 Download history"
echo "  ⚙️  Settings panel"
echo ""
echo "================================================================"
echo ""
echo "Open your browser to: http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================================"
echo ""

python3 web_app.py
