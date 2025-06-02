#!/usr/bin/env python3
"""
Quick benchmark run with known working models
Focus on faster models that we've confirmed work
"""

import os
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fast working models from our tests
QUICK_MODELS = [
    # Fast Anthropic models
    {"provider": "anthropic", "model": "claude-3-haiku-20240307"},
    {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
    
    # Fast OpenAI models  
    {"provider": "openai", "model": "gpt-4o-mini-2024-07-18"},
    {"provider": "openai", "model": "gpt-4.1-nano-2025-04-14"},
    
    # OpenRouter models (usually fast)
    {"provider": "openrouter", "model": "deepseek/deepseek-chat:free"},
    {"provider": "openrouter", "model": "meta-llama/llama-3.3-70b-instruct:free"},
    {"provider": "openrouter", "model": "x-ai/grok-3-beta"},
    
    # Google models
    {"provider": "google", "model": "gemini-2.0-flash-lite"},
    {"provider": "google", "model": "gemini-2.0-flash"},
]

def run_benchmark(model_config):
    """Run benchmark for a single model"""
    provider = model_config["provider"]
    model = model_config["model"]
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing {provider}/{model}")
    logger.info(f"{'='*60}")
    
    cmd = [
        "poetry", "run", "python", "run_benchmark_v3_improved.py",
        "--provider", provider,
        "--model", model,
        "--temperature", "0.7",
        "--scoring-provider", "openai",
        "--scoring-model", "gpt-4o-mini-2024-07-18",  # Use fast scorer
        "--lengths", "3",  # Only test 3-turn sequences (19 total)
        "--limit", "5"  # Only test 5 sequences for quick results
    ]
    
    try:
        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"✓ SUCCESS in {duration:.1f}s")
            return True
        else:
            logger.error(f"✗ FAILED after {duration:.1f}s")
            if result.stderr:
                logger.error(f"Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ TIMEOUT after 600s")
        return False
    except Exception as e:
        logger.error(f"✗ ERROR: {str(e)}")
        return False

def main():
    logger.info("="*60)
    logger.info("SchizoBench Quick Benchmark")
    logger.info(f"Started: {datetime.now()}")
    logger.info(f"Testing {len(QUICK_MODELS)} fast models with 5 sequences each")
    logger.info("="*60)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    success_count = 0
    failed_count = 0
    
    for model_config in QUICK_MODELS:
        if run_benchmark(model_config):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Successful: {success_count}/{len(QUICK_MODELS)}")
    logger.info(f"Failed: {failed_count}/{len(QUICK_MODELS)}")
    
    # Generate dashboard if we have results
    if success_count > 0:
        logger.info("\nGenerating dashboard...")
        try:
            subprocess.run(["poetry", "run", "python", "generate_v3_dashboard_comprehensive.py"], 
                         capture_output=True, text=True, timeout=60)
            logger.info("✓ Dashboard generated")
        except:
            logger.warning("Dashboard generation failed")
    
    logger.info(f"\nCompleted at: {datetime.now()}")

if __name__ == "__main__":
    main()