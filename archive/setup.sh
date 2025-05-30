#!/bin/bash
# SchizoBench Setup Script

echo "SchizoBench Setup"
echo "================="
echo

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "✓ Created .env file"
        echo "⚠️  Please edit .env and add your API keys"
    else
        echo "✗ No .env.example found"
    fi
else
    echo "✓ .env file already exists"
fi

echo
echo "Installing Python dependencies..."
echo

# Check for pip or pip3
if command -v pip &> /dev/null; then
    PIP=pip
elif command -v pip3 &> /dev/null; then
    PIP=pip3
else
    echo "✗ pip not found. Please install Python and pip."
    exit 1
fi

# Install requirements
echo "Running: $PIP install -r requirements.txt"
$PIP install -r requirements.txt

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run: python verify_setup.py"
echo "3. Test with: python run_benchmark_v2.py --provider mock --mode quick"
echo
echo "For detailed instructions, see README.md and USAGE_GUIDE.md"