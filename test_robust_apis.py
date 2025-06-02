#!/usr/bin/env python3
"""
Test the robustness improvements to model interfaces
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_interface import ModelFactory

# Test configurations
test_models = [
    # Anthropic
    ("anthropic", "claude-3-haiku-20240307", "Haiku 3"),
    
    # OpenAI regular
    ("openai", "gpt-4o-mini-2024-07-18", "GPT-4o Mini"),
    
    # OpenAI O-series (should now work!)
    ("openai", "o1-mini-2024-09-12", "O1 Mini"),
    
    # Google
    ("google", "gemini-2.0-flash", "Gemini Flash"),
    
    # OpenRouter
    ("openrouter", "deepseek/deepseek-chat:free", "DeepSeek"),
]

print("Testing Robust Model Interfaces")
print("=" * 50)

for provider, model_name, display_name in test_models:
    print(f"\nTesting {display_name} ({provider}/{model_name})...")
    
    try:
        model = ModelFactory.create(provider, model_name)
        response = model.query("Say 'Hello' in exactly one word.")
        
        if response and not response.startswith("ERROR:"):
            print(f"✓ SUCCESS: {response[:50]}")
        else:
            print(f"✗ FAILED: {response}")
            
    except Exception as e:
        print(f"✗ ERROR: {str(e)[:100]}")

print("\n" + "=" * 50)
print("Test complete!")