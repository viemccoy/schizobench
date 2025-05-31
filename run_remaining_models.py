#!/usr/bin/env python3
"""Run only the remaining models starting with Claude Opus 4 enhanced"""

import subprocess
import logging
import os
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_benchmark(provider, model, system_prompt=None):
    """Run benchmark for a single model"""
    model_str = model.replace("/", "_").replace(":", "_")
    
    # Build command
    cmd = [
        "poetry", "run", "python", "run_benchmark_v3_improved.py",
        "--provider", provider,
        "--model", model,
        "--temperature", "0.7",
        "--scoring-provider", "openai",
        "--scoring-model", "gpt-4.1-2025-04-14"
    ]
    
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    
    logger.info(f"Starting benchmark for {provider}/{model}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)  # 4 hour timeout
        
        if process.returncode == 0:
            logger.info(f"✅ Benchmark completed successfully for {provider}/{model}")
            return True
        else:
            logger.warning(f"⚠️ Benchmark exited with code {process.returncode} for {provider}/{model}")
            # Check if results were saved anyway
            if any(f.startswith(f"schizobench_v3_{model_str}") for f in os.listdir("results_v3")):
                logger.info(f"Found results files for {provider}/{model}")
                return "partial"
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Benchmark timed out for {provider}/{model}")
        return False
    except Exception as e:
        logger.error(f"Error running benchmark: {str(e)}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("Running remaining SchizoBench models")
    logger.info("=" * 80)
    
    # 1. Claude Opus 4 with enhanced system prompt
    logger.info("\nRunning Claude Opus 4 with enhanced system prompt:")
    with open("claude_system_prompt_enhanced.txt", "r") as f:
        enhanced_prompt = f.read()
    
    result = run_benchmark("anthropic", "claude-opus-4-20250514", system_prompt=enhanced_prompt)
    logger.info(f"Claude Opus 4 enhanced: {'Success' if result else 'Failed'}")
    
    time.sleep(5)
    
    # 2. Run OpenAI models
    logger.info("\nRunning OpenAI models:")
    openai_models = [
        "gpt-4.1-2025-04-14",
        "o4-mini-2025-04-16",
        "gpt-4o-2024-08-06"
    ]
    
    for model in openai_models:
        result = run_benchmark("openai", model)
        logger.info(f"{model}: {'Success' if result else 'Failed'}")
        time.sleep(5)
    
    logger.info("\nRemaining benchmarks completed!")
    logger.info("Now running dashboard generation...")
    
    # Generate dashboard
    try:
        subprocess.run(["poetry", "run", "python", "generate_v3_dashboard_dark.py"], check=True)
        logger.info("✅ Dashboard generated successfully!")
    except Exception as e:
        logger.error(f"❌ Dashboard generation failed: {e}")

if __name__ == "__main__":
    main()