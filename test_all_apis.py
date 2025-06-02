#!/usr/bin/env python3
"""
Comprehensive API Test Script for SchizoBench
Tests all providers and models to identify working configurations
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from model_interface import ModelFactory
from api_utils import APIRetryError

# Test configurations
TEST_CONFIGS = {
    "anthropic": [
        # Start with faster models
        ("claude-3-haiku-20240307", "Haiku 3"),
        ("claude-3-sonnet-20240229", "Sonnet 3"), 
        ("claude-3-opus-20240229", "Opus 3"),
        ("claude-3-5-haiku-20241022", "Haiku 3.5"),
        ("claude-3-5-sonnet-20240620", "Sonnet 3.5 v1"),
        ("claude-3-5-sonnet-20241022", "Sonnet 3.5 v2"),
        ("claude-3-7-sonnet-20250219", "Sonnet 3.7"),
        ("claude-sonnet-4-20250514", "Sonnet 4"),
        ("claude-opus-4-20250514", "Opus 4"),
    ],
    "openai": [
        # Start with mini models
        ("gpt-4o-mini-2024-07-18", "GPT-4o Mini"),
        ("gpt-4.1-nano-2025-04-14", "GPT-4.1 Nano"),
        ("gpt-4.1-mini-2025-04-14", "GPT-4.1 Mini"),
        ("gpt-4o-2024-08-06", "GPT-4o"),
        ("gpt-4.1-2025-04-14", "GPT-4.1"),
        # O-series (need special handling)
        ("o1-mini-2024-09-12", "O1 Mini"),
        ("o1-2024-12-17", "O1"),
        ("o3-mini-2025-01-31", "O3 Mini"),
        ("o4-mini-2025-04-16", "O4 Mini"),
        ("o3-2025-04-16", "O3"),
    ],
    "google": [
        ("gemini-2.0-flash-lite", "Gemini 2.0 Flash Lite"),
        ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ("gemini-2.5-flash-preview-05-20", "Gemini 2.5 Flash Preview"),
        ("gemini-2.5-pro-preview-05-06", "Gemini 2.5 Pro Preview"),
    ],
    "openrouter": [
        # Test a few key models
        ("deepseek/deepseek-chat:free", "DeepSeek Chat"),
        ("x-ai/grok-3-beta", "Grok 3 Beta"),
        ("meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B"),
        ("nousresearch/hermes-3-llama-3.1-70b", "Hermes 3"),
    ]
}

def test_single_model(provider: str, model_name: str, display_name: str) -> Tuple[bool, float, str]:
    """Test a single model and return (success, response_time, error_msg)"""
    start_time = time.time()
    
    try:
        # Special handling for O-series models
        kwargs = {}
        if provider == "openai" and model_name.startswith("o"):
            kwargs['temperature'] = 1.0
            
        model = ModelFactory.create(provider, model_name, **kwargs)
        
        # Simple test query
        response = model.query("Say 'Hello SchizoBench' in exactly 3 words.")
        
        response_time = time.time() - start_time
        
        if response and not response.startswith("ERROR:"):
            return True, response_time, response[:50]
        else:
            return False, response_time, f"Invalid response: {response[:100]}"
            
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)[:200]
        return False, response_time, error_msg

def test_provider(provider: str, models: List[Tuple[str, str]]) -> Dict:
    """Test all models for a provider"""
    results = {
        "provider": provider,
        "total": len(models),
        "working": 0,
        "failed": 0,
        "models": []
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {provider.upper()} Models")
    logger.info(f"{'='*60}")
    
    for model_name, display_name in models:
        logger.info(f"\nTesting {display_name} ({model_name})...")
        
        success, response_time, result = test_single_model(provider, model_name, display_name)
        
        status = "✓" if success else "✗"
        status_text = "SUCCESS" if success else "FAILED"
        
        model_result = {
            "model": model_name,
            "display_name": display_name,
            "success": success,
            "response_time": response_time,
            "result": result
        }
        
        results["models"].append(model_result)
        
        if success:
            results["working"] += 1
            logger.info(f"  {status} {status_text} - {response_time:.2f}s - {result}")
        else:
            results["failed"] += 1
            logger.error(f"  {status} {status_text} - {response_time:.2f}s - {result}")
        
        # Small delay between tests
        time.sleep(1)
    
    return results

def main():
    """Run comprehensive API tests"""
    logger.info("="*60)
    logger.info("SchizoBench API Test Suite")
    logger.info(f"Started: {datetime.now()}")
    logger.info("="*60)
    
    # Check environment variables
    logger.info("\nChecking API Keys:")
    api_keys = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY")
    }
    
    for key_name, key_value in api_keys.items():
        status = "✓ SET" if key_value else "✗ NOT SET"
        logger.info(f"  {key_name}: {status}")
    
    # Test each provider
    all_results = {}
    
    for provider, models in TEST_CONFIGS.items():
        if provider == "anthropic" and not api_keys["ANTHROPIC_API_KEY"]:
            logger.warning(f"\nSkipping {provider} - No API key")
            continue
        if provider == "openai" and not api_keys["OPENAI_API_KEY"]:
            logger.warning(f"\nSkipping {provider} - No API key")
            continue
        if provider == "google" and not api_keys["GOOGLE_API_KEY"]:
            logger.warning(f"\nSkipping {provider} - No API key")
            continue
        if provider == "openrouter" and not api_keys["OPENROUTER_API_KEY"]:
            logger.warning(f"\nSkipping {provider} - No API key")
            continue
            
        results = test_provider(provider, models)
        all_results[provider] = results
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    total_working = 0
    total_failed = 0
    
    for provider, results in all_results.items():
        logger.info(f"\n{provider.upper()}:")
        logger.info(f"  Working: {results['working']}/{results['total']}")
        logger.info(f"  Failed: {results['failed']}/{results['total']}")
        
        total_working += results['working']
        total_failed += results['failed']
        
        # Show working models
        if results['working'] > 0:
            logger.info(f"  Working models:")
            for model in results['models']:
                if model['success']:
                    logger.info(f"    ✓ {model['display_name']} ({model['response_time']:.2f}s)")
        
        # Show failed models
        if results['failed'] > 0:
            logger.info(f"  Failed models:")
            for model in results['models']:
                if not model['success']:
                    logger.info(f"    ✗ {model['display_name']}: {model['result'][:50]}...")
    
    logger.info(f"\nTOTAL: {total_working} working, {total_failed} failed")
    
    # Save results
    import json
    with open('api_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': all_results,
            'summary': {
                'total_working': total_working,
                'total_failed': total_failed
            }
        }, f, indent=2)
    
    logger.info("\nResults saved to api_test_results.json")

if __name__ == "__main__":
    main()