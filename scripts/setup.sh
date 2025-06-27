#!/bin/bash

# EdutainmentForge Setup Script
# Installs dependencies and sets up the development environment

set -e

echo "🎙️  Setting up EdutainmentForge..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "📥 Installing development dependencies..."
pip install -r requirements-dev.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p output
mkdir -p temp
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
fi

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the application: python src/main.py"
echo ""
echo "For development:"
echo "- Run tests: pytest tests/"
echo "- Format code: black src/ tests/"
echo "- Check style: flake8 src/ tests/"
