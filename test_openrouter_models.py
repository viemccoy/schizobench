#!/usr/bin/env python3
"""
Test script for OpenRouter models
Tests all configured models with simple queries
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_interface import OpenRouterInterface
from api_utils import APIRetryError

# OpenRouter models to test
OPENROUTER_MODELS = [
    "deepseek/deepseek-r1-0528:free",
    "x-ai/grok-3-beta",
    "x-ai/grok-3-mini-beta",
    "x-ai/grok-2-1212",
    "deepseek/deepseek-chat-v3-0324:free",
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat:free",
    "meta-llama/llama-4-maverick:free",
    "meta-llama/llama-4-scout:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-70b",
    "nousresearch/hermes-3-llama-3.1-405b",
    "meta-llama/llama-3.1-405b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/llama-3-70b-instruct"
]

# Test prompts
TEST_PROMPTS = [
    "Hello! Can you briefly introduce yourself?",
    "What is 2 + 2?",
    "Please tell me a short joke.",
    "Can you explain what schizophrenia is in one sentence?"
]

def test_model(model_name: str):
    """Test a single OpenRouter model"""
    logger.info(f"\nTesting model: {model_name}")
    
    # Remove :free suffix for display
    display_name = model_name.replace(":free", "")
    
    try:
        # Initialize model interface
        interface = OpenRouterInterface(
            model_name=model_name
        )
        
        # Test each prompt
        for i, prompt in enumerate(TEST_PROMPTS, 1):
            logger.info(f"  Test {i}/4: {prompt[:50]}...")
            
            try:
                response = interface.query(prompt)
                if response and not response.startswith("ERROR:"):
                    logger.info(f"    ✓ Success - Response length: {len(response)} chars")
                    if i == 1:  # Show first response preview
                        preview = response[:150].replace('\n', ' ')
                        logger.info(f"    Preview: {preview}...")
                else:
                    logger.warning(f"    ✗ Failed: {response}")
                    
            except Exception as e:
                logger.error(f"    ✗ Error: {type(e).__name__}: {str(e)}")
        
        # Test with system prompt
        logger.info("  Testing with system prompt...")
        try:
            response = interface.query(
                "What is your purpose?",
                system_prompt="You are a helpful AI assistant focused on mental health safety."
            )
            if response and not response.startswith("ERROR:"):
                logger.info("    ✓ System prompt test passed")
            else:
                logger.warning("    ✗ System prompt test failed")
        except Exception as e:
            logger.error(f"    ✗ System prompt error: {str(e)}")
        
        logger.info(f"  ✓ Model {display_name} testing complete")
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Failed to initialize {display_name}: {type(e).__name__}: {str(e)}")
        return False

def main():
    """Main test runner"""
    logger.info("=" * 70)
    logger.info("OpenRouter Model Testing Suite")
    logger.info("=" * 70)
    
    # Check for API key and set if not present
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
        os.environ["OPENROUTER_API_KEY"] = api_key
        logger.info("Set OpenRouter API key from hardcoded value")
    else:
        logger.info("Using API key from environment")
    
    # Track results
    successful = []
    failed = []
    
    # Test each model
    for model in OPENROUTER_MODELS:
        success = test_model(model)
        if success:
            successful.append(model)
        else:
            failed.append(model)
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total models tested: {len(OPENROUTER_MODELS)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info("\nSuccessful models:")
        for model in successful:
            display_name = model.replace(":free", "")
            logger.info(f"  ✓ {display_name}")
    
    if failed:
        logger.info("\nFailed models:")
        for model in failed:
            display_name = model.replace(":free", "")
            logger.info(f"  ✗ {display_name}")
    
    # Return exit code based on results
    return 0 if len(failed) == 0 else 1

if __name__ == "__main__":
    exit(main())