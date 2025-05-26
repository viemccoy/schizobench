#!/bin/bash
# SchizoBench Poetry Setup Script

echo "SchizoBench Poetry Setup"
echo "======================="
echo

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "✓ Poetry installed"
    echo "  Please add Poetry to your PATH if needed:"
    echo "  export PATH=\"$HOME/.local/bin:\$PATH\""
    echo
else
    echo "✓ Poetry is already installed"
fi

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
echo "Installing dependencies with Poetry..."
poetry install

echo
echo "Setting up pre-commit hooks..."
poetry run pre-commit install 2>/dev/null || echo "  (pre-commit not configured)"

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "1. Edit .env and add your API keys (if not done already)"
echo "2. Activate the Poetry shell: poetry shell"
echo "3. Verify setup: poetry run verify-setup"
echo "4. Run quick test: poetry run schizobench-v2 --provider mock --mode quick"
echo
echo "Or use the Makefile:"
echo "  make verify      # Verify setup"
echo "  make run-mock    # Test with mock provider"
echo "  make run-quick   # Quick test with real API"
echo
echo "For detailed instructions, see README.md and USAGE_GUIDE.md"