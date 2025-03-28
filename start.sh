#!/bin/bash

# Exit on error
set -e

echo "Setting up Document Analysis Dashboard..."

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "Installing frontend dependencies..."
pip install -r frontend/requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p backend/cache
mkdir -p backend/uploads
mkdir -p frontend/temp_uploads

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo "MISTRAL_API_KEY=your_mistral_api_key" > .env
    echo "Please update the .env file with your Mistral AI API key"
    exit 1
fi

# Start backend server in the background
echo "Starting backend server..."
cd backend
uvicorn app:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend server
echo "Starting frontend server..."
cd frontend
python app.py
FRONTEND_PID=$!

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT 