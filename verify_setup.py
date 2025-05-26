#!/usr/bin/env python3
"""
Verify SchizoBench setup and API keys
"""

import os
import sys

try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  Warning: python-dotenv not installed. Using system environment variables only.")
    print("   Install with: pip install python-dotenv")
    print()

from schizobench.model_interface import ModelFactory

def verify_setup():
    """Check if everything is set up correctly"""
    print("SchizoBench Setup Verification")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print()
    
    # Check API keys
    print("API Keys Status:")
    print("-" * 30)
    
    keys = {
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "OPENAI_API_KEY": "OpenAI (GPT)",
        "GOOGLE_API_KEY": "Google (Gemini)"
    }
    
    available_providers = []
    
    for env_var, provider_name in keys.items():
        key = os.getenv(env_var)
        if key:
            # Mask the key for security
            masked_key = key[:10] + "..." + key[-4:] if len(key) > 14 else "***"
            print(f"✓ {provider_name}: {masked_key}")
            available_providers.append(provider_name.split()[0].lower())
        else:
            print(f"✗ {provider_name}: Not found")
    
    print()
    
    # Test creating model interfaces
    print("Testing Model Interfaces:")
    print("-" * 30)
    
    # Always test mock
    try:
        mock_model = ModelFactory.create("mock")
        print("✓ Mock model: Ready")
    except Exception as e:
        print(f"✗ Mock model: {e}")
    
    # Test available providers
    for provider in available_providers:
        try:
            if provider == "anthropic":
                model = ModelFactory.create(provider, "claude-3-opus-20240229")
            elif provider == "openai":
                model = ModelFactory.create(provider, "gpt-4")
            elif provider == "google":
                model = ModelFactory.create(provider, "gemini-pro")
            print(f"✓ {provider.title()} model: Ready")
        except Exception as e:
            print(f"✗ {provider.title()} model: {e}")
    
    print()
    
    # Check required packages
    print("Required Packages:")
    print("-" * 30)
    
    packages = {
        "anthropic": "Anthropic SDK",
        "openai": "OpenAI SDK",
        "google.generativeai": "Google Generative AI",
        "matplotlib": "Matplotlib (visualizations)",
        "seaborn": "Seaborn (visualizations)",
        "numpy": "NumPy",
        "dotenv": "python-dotenv"
    }
    
    for package, name in packages.items():
        try:
            if package == "google.generativeai":
                import google.generativeai
            elif package == "dotenv":
                import dotenv
            else:
                __import__(package)
            print(f"✓ {name}: Installed")
        except ImportError:
            print(f"✗ {name}: Not installed (pip install {package})")
    
    print()
    print("=" * 50)
    
    if available_providers:
        print(f"✅ Setup complete! You can test with: {', '.join(available_providers)}")
        print("\nExample commands:")
        for provider in available_providers[:2]:  # Show first 2 examples
            print(f"  python run_benchmark_v2.py --provider {provider} --mode quick")
    else:
        print("⚠️  No API keys configured. You can still test with:")
        print("  python run_benchmark_v2.py --provider mock --mode quick")
    
    print("\nFor full documentation, see USAGE_GUIDE.md")

def main():
    """Entry point for Poetry script"""
    verify_setup()


if __name__ == "__main__":
    main()