#!/bin/bash

echo "🚀 Starting TikZ2SVG Development Server..."

# Kill existing Flask processes
echo "🔄 Cleaning up existing processes..."
pkill -f "flask run" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

echo "🌐 Starting Flask app on http://localhost:5173"
echo "📱 Email test: http://localhost:5173/email-test"
echo "🛑 Press Ctrl+C to stop"

# Run Flask development server
flask run --host=0.0.0.0 --port=5173
