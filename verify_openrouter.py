#!/usr/bin/env python3
"""
Quick verification script for OpenRouter integration
Tests one model from each category to ensure everything works
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model_interface import ModelFactory

# Set API key if not in environment
if not os.getenv("OPENROUTER_API_KEY"):
    # Load from .env file or environment
    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Error: OPENROUTER_API_KEY not found in environment")
        sys.exit(1)

def test_openrouter_integration():
    """Test OpenRouter integration with one model from each category"""
    
    # Test models (one from each category)
    test_models = [
        "deepseek/deepseek-chat:free",     # DeepSeek
        "x-ai/grok-3-beta",                 # X.AI (using grok-3 instead of grok-2-mini which is not available)
        "meta-llama/llama-3.3-70b-instruct:free",  # Meta Llama
        "nousresearch/hermes-3-llama-3.1-70b"      # NousResearch
    ]
    
    logger.info("Testing OpenRouter integration...")
    logger.info("=" * 60)
    
    success_count = 0
    
    for model_name in test_models:
        logger.info(f"\nTesting {model_name}...")
        
        try:
            # Create model interface through factory
            interface = ModelFactory.create("openrouter", model_name)
            
            # Test simple query
            response = interface.query("Say 'Hello SchizoBench!' in exactly 3 words.")
            
            if response and not response.startswith("ERROR:"):
                logger.info(f"✓ Success! Response: {response[:100]}")
                
                # Get model info to verify display name
                info = interface.get_model_info()
                logger.info(f"  Display name: {info['model']}")
                
                success_count += 1
            else:
                logger.error(f"✗ Failed: {response}")
                
        except Exception as e:
            logger.error(f"✗ Error: {type(e).__name__}: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Results: {success_count}/{len(test_models)} models working")
    
    if success_count == len(test_models):
        logger.info("\n✅ OpenRouter integration verified successfully!")
        logger.info("You can now run the full benchmark with:")
        logger.info("  python run_overnight.py")
        return True
    else:
        logger.warning("\n⚠️  Some models failed. Check your API key and connection.")
        return False

if __name__ == "__main__":
    success = test_openrouter_integration()
    exit(0 if success else 1)