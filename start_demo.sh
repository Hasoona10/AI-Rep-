#!/bin/bash
# Quick start script for phone call demo

echo "🚀 Starting AI Receptionist Phone Demo"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your credentials first."
    echo "See STEP_BY_STEP_SETUP.md for instructions."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip install -q fastapi uvicorn python-dotenv twilio openai chromadb pydantic httpx websockets
fi

echo "✅ Starting server on http://localhost:8000"
echo ""
echo "📝 Next steps:"
echo "1. Open a NEW terminal and run: ngrok http 8000"
echo "2. Copy the ngrok HTTPS URL"
echo "3. Configure Twilio webhooks with that URL"
echo "4. Call your Twilio number!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python run.py


