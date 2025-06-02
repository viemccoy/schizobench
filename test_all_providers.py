#!/usr/bin/env python3
"""Test one model from each provider to ensure everything works"""

import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from model_interface import ModelFactory
from run_benchmark_live import run_live_benchmark

# Test configurations
TEST_MODELS = [
    ("anthropic", "claude-3-haiku-20240307"),
    ("openai", "gpt-4o-mini"),
    ("google", "gemini-2.0-flash-exp"),
]

# Single test sequence for quick validation
TEST_SEQUENCE = ["v3_3t_identity_oracle"]

def test_provider(provider: str, model: str):
    """Test a single provider/model combination"""
    print(f"\n{'='*60}")
    print(f"Testing {provider} / {model}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # First test that we can create the model
        print(f"Creating model interface...")
        model_interface = ModelFactory.create(provider=provider, model_name=model)
        print(f"✓ Model created successfully")
        
        # Test a simple query
        print(f"Testing simple query...")
        response = model_interface.query("Hello, please respond with 'test successful'")
        print(f"✓ Response received: {response[:50]}...")
        
        # Now run the benchmark test
        print(f"\nRunning benchmark test...")
        run_live_benchmark(provider, model, TEST_SEQUENCE)
        
        print(f"\n✓ {provider}/{model} test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error testing {provider}/{model}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("SchizoBench Provider Test Suite")
    print("Testing one model from each provider...")
    
    results = {}
    for provider, model in TEST_MODELS:
        results[f"{provider}/{model}"] = test_provider(provider, model)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for key, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{key}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All providers tested successfully!")
        print("Ready to run overnight benchmark.")
    else:
        print("\n✗ Some providers failed. Please check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()