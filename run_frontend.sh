#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "frontend/venv" ]; then
    echo "Creating virtual environment for frontend..."
    python3 -m venv frontend/venv
fi

# Activate virtual environment
source frontend/venv/bin/activate

# Install frontend requirements
echo "Installing frontend requirements..."
pip install -r frontend/requirements.txt

# Run the Flask frontend
echo "Starting Flask frontend..."
cd frontend
python app.py 