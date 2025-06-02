#!/usr/bin/env python3
"""Test script to verify access to OpenAI models"""

import os
import sys
from openai import OpenAI
from datetime import datetime
import time

# Models to test
OPENAI_MODELS_TO_TEST = [
    "o3-2025-04-16",
    "o1-2024-12-17", 
    "o3-mini-2025-01-31",
    "o4-mini-2025-04-16",
    "gpt-4.1-mini-2025-04-14",
    "gpt-4.1-nano-2025-04-14",
    "gpt-4o-mini-2024-07-18",
    "o1-mini-2024-09-12"
]

def test_model_access(client, model_name):
    """Test if we have access to a specific model"""
    print(f"\nTesting {model_name}...")
    
    try:
        # Check if it's an o-series model
        is_o_series = model_name.startswith(('o1-', 'o3-', 'o4-'))
        
        # Build parameters based on model type
        params = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Say 'Hello! I am working.' in exactly 4 words."}
            ]
        }
        
        if is_o_series:
            params["max_completion_tokens"] = 50
            # o-series models don't support temperature
        else:
            params["max_tokens"] = 50
            params["temperature"] = 0.7
        
        # Simple test prompt
        response = client.chat.completions.create(**params)
        
        result = response.choices[0].message.content
        print(f"✅ {model_name}: SUCCESS - Response: {result}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "model" in error_msg.lower() and "does not exist" in error_msg.lower():
            print(f"❌ {model_name}: MODEL NOT FOUND")
        elif "rate" in error_msg.lower():
            print(f"⚠️  {model_name}: RATE LIMITED (but model exists)")
            return True  # Model exists but we're rate limited
        else:
            print(f"❌ {model_name}: ERROR - {error_msg}")
        return False

def main():
    # Try to load from .env file first
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("No OPENAI_API_KEY found in environment.")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        print("Or add it to your .env file")
        sys.exit(1)
    
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    print("="*60)
    print("OpenAI Model Access Test")
    print(f"Testing {len(OPENAI_MODELS_TO_TEST)} models")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test each model
    accessible_models = []
    inaccessible_models = []
    
    for model in OPENAI_MODELS_TO_TEST:
        if test_model_access(client, model):
            accessible_models.append(model)
        else:
            inaccessible_models.append(model)
        
        # Small delay to avoid rate limits
        time.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\n✅ Accessible models ({len(accessible_models)}):")
    for model in accessible_models:
        print(f"   - {model}")
    
    if inaccessible_models:
        print(f"\n❌ Inaccessible models ({len(inaccessible_models)}):")
        for model in inaccessible_models:
            print(f"   - {model}")
    
    print(f"\nTotal: {len(accessible_models)}/{len(OPENAI_MODELS_TO_TEST)} models accessible")
    
    # Write results to file
    with open("openai_models_test_results.txt", "w") as f:
        f.write(f"OpenAI Model Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        f.write("Accessible models:\n")
        for model in accessible_models:
            f.write(f"- {model}\n")
        f.write("\nInaccessible models:\n")
        for model in inaccessible_models:
            f.write(f"- {model}\n")
    
    print("\nResults saved to: openai_models_test_results.txt")

if __name__ == "__main__":
    main()