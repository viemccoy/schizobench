#!/usr/bin/env python3
"""
Robust overnight benchmark runner with enhanced error handling and recovery
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
import json
import traceback

# Setup logging
log_dir = "benchmark_logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"overnight_run_{timestamp}.log")

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Model configurations with retry settings
MODELS_TO_TEST = [
    # Anthropic models
    {"provider": "anthropic", "model": "claude-opus-4-20250514", "retries": 3},
    {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "retries": 3},
    {"provider": "anthropic", "model": "claude-3-7-sonnet-20250219", "retries": 3},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022", "retries": 3},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "retries": 3},
    {"provider": "anthropic", "model": "claude-3-opus-20240229", "retries": 3},
    {"provider": "anthropic", "model": "claude-3-sonnet-20240229", "retries": 3},
    
    # Claude Opus 4 with enhanced prompt
    {"provider": "anthropic", "model": "claude-opus-4-20250514", "retries": 3, "enhanced_prompt": True},
    
    # OpenAI models
    {"provider": "openai", "model": "gpt-4.1-2025-04-14", "retries": 3},
    {"provider": "openai", "model": "o4-mini-2025-04-16", "retries": 3, "temperature": 1.0},
    {"provider": "openai", "model": "gpt-4o-2024-08-06", "retries": 3},
]

def run_single_benchmark(provider, model, temperature=0.7, retry_count=0, max_retries=3, enhanced_prompt=False):
    """Run benchmark for a single model with retry logic"""
    
    model_str = model.replace(".", "-")
    logger.info(f"Starting benchmark for {provider}/{model} (attempt {retry_count + 1}/{max_retries})")
    if enhanced_prompt:
        logger.info("Using enhanced system prompt")
    
    try:
        # Build command directly instead of using environment vars
        cmd = [
            "poetry", "run", "python", "run_benchmark_v3_improved.py",
            "--provider", provider,
            "--model", model,
            "--temperature", str(temperature),
            "--scoring-provider", "openai",
            "--scoring-model", "gpt-4.1-2025-04-14"
        ]
        
        # Add enhanced prompt if needed
        if enhanced_prompt:
            enhanced_prompt_path = os.path.join("archive", "claude_system_prompt_enhanced.txt")
            if os.path.exists(enhanced_prompt_path):
                with open(enhanced_prompt_path, "r") as f:
                    prompt_content = f.read().strip()
                cmd.extend(["--system-prompt", prompt_content])
            else:
                logger.error(f"Enhanced prompt file not found at {enhanced_prompt_path}")
                return False
        
        # Run the benchmark
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout per model
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Successfully completed {provider}/{model}")
            return True
        else:
            logger.warning(f"✗ Failed {provider}/{model} with exit code {result.returncode}")
            logger.warning(f"Error output: {result.stderr[:500]}")
            
            # Check if partial results were generated
            if check_partial_results(model_str):
                logger.info(f"⚠ Partial results found for {provider}/{model}")
                return True
            
            if retry_count < max_retries - 1:
                wait_time = 30 * (retry_count + 1)  # Exponential backoff
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                return run_single_benchmark(provider, model, temperature, retry_count + 1, max_retries, enhanced_prompt)
            
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Timeout for {provider}/{model} after 2 hours")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error for {provider}/{model}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def check_partial_results(model_str):
    """Check if partial results exist for a model"""
    results_dir = "results_v3"
    if not os.path.exists(results_dir):
        return False
    
    for file in os.listdir(results_dir):
        if model_str in file and file.endswith(".json"):
            file_path = os.path.join(results_dir, file)
            if os.path.getsize(file_path) > 1000:  # Non-trivial size
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if "sequences" in data and len(data["sequences"]) > 0:
                            return True
                except:
                    pass
    return False

def main():
    """Main overnight benchmark runner"""
    logger.info("=" * 70)
    logger.info("SchizoBench Overnight Benchmark Run")
    logger.info("=" * 70)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set - OpenAI models will fail")
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not set - Anthropic models will fail")
    
    # Track results
    successful = []
    failed = []
    partial = []
    
    # Run benchmarks
    total_models = len(MODELS_TO_TEST)
    for i, config in enumerate(MODELS_TO_TEST, 1):
        logger.info(f"\n--- Model {i}/{total_models} ---")
        
        provider = config["provider"]
        model = config["model"]
        temperature = config.get("temperature", 0.7)
        max_retries = config.get("retries", 3)
        enhanced_prompt = config.get("enhanced_prompt", False)
        
        success = run_single_benchmark(provider, model, temperature, max_retries=max_retries, enhanced_prompt=enhanced_prompt)
        
        if success:
            if check_partial_results(model.replace(".", "-")):
                if enhanced_prompt:
                    successful.append(f"{provider}/{model} (enhanced)")
                else:
                    successful.append(f"{provider}/{model}")
            else:
                if enhanced_prompt:
                    partial.append(f"{provider}/{model} (enhanced)")
                else:
                    partial.append(f"{provider}/{model}")
        else:
            if enhanced_prompt:
                failed.append(f"{provider}/{model} (enhanced)")
            else:
                failed.append(f"{provider}/{model}")
        
        # Brief pause between models
        if i < total_models:
            time.sleep(10)
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total models tested: {total_models}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Partial results: {len(partial)}")
    logger.info(f"Failed: {len(failed)}")
    
    if successful:
        logger.info("\nSuccessful models:")
        for model in successful:
            logger.info(f"  ✓ {model}")
    
    if partial:
        logger.info("\nPartial results:")
        for model in partial:
            logger.info(f"  ⚠ {model}")
    
    if failed:
        logger.info("\nFailed models:")
        for model in failed:
            logger.info(f"  ✗ {model}")
    
    # Generate dashboard if we have results
    if successful or partial:
        logger.info("\nGenerating dashboard...")
        try:
            # Try comparison dashboard first (if we have enhanced prompt results)
            result = subprocess.run(["poetry", "run", "python", "generate_v3_dashboard_comparison.py"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✓ Comparison dashboard generated successfully")
                logger.info("Check: results_v3/visualizations/schizobench_v3_dashboard_comparison.html")
            else:
                logger.info("Comparison dashboard not available, trying standard dashboard...")
                # Fall back to standard dashboard
                result = subprocess.run(["poetry", "run", "python", "generate_v3_dashboard_dark.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("✓ Standard dashboard generated successfully")
                else:
                    logger.warning("✗ Dashboard generation failed - run manually later")
        except:
            logger.warning("✗ Dashboard generation failed - run manually later")
    
    logger.info(f"\nComplete log: {log_file}")
    logger.info("Results directory: results_v3/")
    logger.info("Dashboard directory: dashboards/")
    logger.info("\nOvernight benchmark run complete!")

if __name__ == "__main__":
    main()