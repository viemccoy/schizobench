#!/usr/bin/env python3
"""Test the streamlined ModelFactory"""

from dotenv import load_dotenv
load_dotenv()

from model_interface import ModelFactory

# Test factory info
print("ModelFactory Info:")
info = ModelFactory.get_provider_info()
print(f"  Providers: {', '.join(info['providers'])}")
print(f"  Aliases: {info['aliases']}")
print(f"  Default models: {info['defaults']}")

print("\nTesting model creation:")

# Test each provider
test_cases = [
    ("anthropic", "claude-3-haiku-20240307"),
    ("openai", "gpt-4o-mini"),
    ("google", "gemini-2.0-flash-exp"),
    ("claude", None),  # Test alias with default model
    ("gpt", "gpt-4.1-2025-04-14"),  # Test alias with specific model
]

for provider, model in test_cases:
    try:
        print(f"\n{provider} / {model or 'default'}:")
        interface = ModelFactory.create(provider=provider, model_name=model)
        info = interface.get_model_info()
        print(f"  ✓ Created: {info.get('model', info.get('name', 'Unknown'))} (provider: {info.get('provider', 'N/A')})")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Test error handling
print("\n\nTesting error handling:")
try:
    ModelFactory.create("invalid_provider")
except ValueError as e:
    print(f"  ✓ Correctly caught invalid provider: {e}")

# Test convenience method
print("\n\nTesting create_from_env:")
try:
    interface = ModelFactory.create_from_env("openai", "gpt-4o-mini")
    print(f"  ✓ Created from environment")
except Exception as e:
    print(f"  ✗ Error: {e}")