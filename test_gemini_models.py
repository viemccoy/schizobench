#!/usr/bin/env python3
"""Test script to verify access to Google Gemini models"""

import os
import sys
from datetime import datetime
import time

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Models to test
GEMINI_MODELS_TO_TEST = [
    "gemini-2.5-pro-preview-05-06",
    "gemini-2.5-flash-preview-05-20",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite"
]

def test_model_access(api_key, model_name):
    """Test if we have access to a specific model"""
    print(f"\nTesting {model_name}...")
    
    try:
        import google.generativeai as genai
        
        # Configure API
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel(model_name)
        
        # Simple test prompt
        response = model.generate_content("Say 'Hello! I am working.' in exactly 4 words.")
        
        result = response.text
        print(f"✅ {model_name}: SUCCESS - Response: {result[:100]}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "model" in error_msg.lower() and "not found" in error_msg.lower():
            print(f"❌ {model_name}: MODEL NOT FOUND")
        elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
            print(f"⚠️  {model_name}: RATE LIMITED (but model exists)")
            return True  # Model exists but we're rate limited
        else:
            print(f"❌ {model_name}: ERROR - {error_msg}")
        return False

def main():
    # Get API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("No GOOGLE_API_KEY found in environment.")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    
    print("="*60)
    print("Google Gemini Model Access Test")
    print(f"Testing {len(GEMINI_MODELS_TO_TEST)} models")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test each model
    accessible_models = []
    inaccessible_models = []
    
    for model in GEMINI_MODELS_TO_TEST:
        if test_model_access(api_key, model):
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
    
    print(f"\nTotal: {len(accessible_models)}/{len(GEMINI_MODELS_TO_TEST)} models accessible")
    
    # Write results to file
    with open("gemini_models_test_results.txt", "w") as f:
        f.write(f"Gemini Model Test Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        f.write("Accessible models:\n")
        for model in accessible_models:
            f.write(f"- {model}\n")
        f.write("\nInaccessible models:\n")
        for model in inaccessible_models:
            f.write(f"- {model}\n")
    
    print("\nResults saved to: gemini_models_test_results.txt")

if __name__ == "__main__":
    main()