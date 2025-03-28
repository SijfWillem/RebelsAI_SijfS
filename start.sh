#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Download spaCy model if not already downloaded
echo "Checking spaCy model..."
python -m spacy download en_core_web_sm

# Check if Client Data directory exists
if [ ! -d "Client Data" ]; then
    echo "Error: 'Client Data' directory not found!"
    echo "Please ensure the 'Client Data' directory exists in the current directory."
    exit 1
fi

# Run the server
echo "Starting server..."
python run.py 