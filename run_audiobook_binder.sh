#!/bin/bash

# AudioBook Binder Runner Script
# This script activates the virtual environment and runs the audiobook binder

echo "🚀 Starting AudioBook Binder..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "audiobook_env" ]; then
    echo "❌ Error: Virtual environment 'audiobook_env' not found!"
    echo "Please make sure you're running this script from the correct directory."
    exit 1
fi

# Check if audiobook_binder.py exists
if [ ! -f "audiobook_binder.py" ]; then
    echo "❌ Error: audiobook_binder.py not found!"
    echo "Please make sure you're running this script from the correct directory."
    exit 1
fi

# Check if AudioBooks directory exists
if [ ! -d "AudioBooks" ]; then
    echo "❌ Error: AudioBooks directory not found!"
    echo "Please make sure the AudioBooks folder exists."
    exit 1
fi

echo "📁 Input directory: AudioBooks/"
echo "🐍 Activating virtual environment..."

# Activate virtual environment
source audiobook_env/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate virtual environment!"
    exit 1
fi

echo "✅ Virtual environment activated"
echo "🎵 Running AudioBook Binder..."
echo ""

# Run the audiobook binder with AudioBooks as input directory
python audiobook_binder.py AudioBooks

# Store the exit code
EXIT_CODE=$?

echo ""
echo "🔄 Deactivating virtual environment..."
deactivate

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ AudioBook Binder completed successfully!"
else
    echo "❌ AudioBook Binder exited with error code: $EXIT_CODE"
fi

echo "👋 Script finished."
