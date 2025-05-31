#!/usr/bin/env python3
"""Run the final 4 models (Claude Opus 4 enhanced + 3 OpenAI) and generate dashboard."""

import subprocess
import time
import os
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
log_file = f"final_4_models_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_benchmark(provider, model, temperature=0.7, system_prompt=None):
    """Run a single benchmark."""
    cmd = [
        "poetry", "run", "python", "run_benchmark_v3_improved.py",
        "--provider", provider,
        "--model", model,
        "--temperature", str(temperature),
        "--scoring-provider", "openai",
        "--scoring-model", "gpt-4.1-2025-04-14"
    ]
    
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])
    
    logger.info(f"Starting benchmark for {provider}/{model}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✅ {model}: Success")
    else:
        logger.warning(f"⚠️ Benchmark exited with code {result.returncode} for {provider}/{model}")
        if result.stderr:
            logger.error(f"Error output: {result.stderr}")
    
    # Check if results were created
    results_dir = Path("results_v3")
    pattern = f"*{model}*"
    if list(results_dir.glob(pattern)):
        logger.info(f"Found results files for {provider}/{model}")
    else:
        logger.error(f"No results files found for {provider}/{model}")
    
    return result.returncode == 0

def main():
    logger.info("="*80)
    logger.info("Running final 4 SchizoBench models")
    logger.info("="*80)
    
    # Load enhanced system prompt for Claude Opus 4
    enhanced_prompt_path = Path("archive/claude_system_prompt_enhanced.txt")
    if enhanced_prompt_path.exists():
        enhanced_prompt = enhanced_prompt_path.read_text().strip()
        logger.info("Loaded enhanced system prompt")
    else:
        logger.error("Enhanced prompt file not found!")
        return
    
    # Define models to run
    models = [
        ("anthropic", "claude-opus-4-20250514", enhanced_prompt),  # With enhanced prompt
        ("openai", "gpt-4.1-2025-04-14", None),
        ("openai", "o4-mini-2025-04-16", None),
        ("openai", "gpt-4o-2024-08-06", None),
    ]
    
    # Run each model
    for provider, model, system_prompt in models:
        logger.info(f"\nRunning {model}...")
        if system_prompt:
            logger.info("Using enhanced system prompt")
        
        success = run_benchmark(provider, model, system_prompt=system_prompt)
        
        if not success:
            logger.warning(f"Benchmark failed for {model}, continuing with next model...")
        
        # Small delay between models
        time.sleep(5)
    
    logger.info("\n" + "="*80)
    logger.info("All models completed!")
    logger.info("="*80)
    
    # Generate dashboard with Opus 4 comparison
    logger.info("\nGenerating enhanced comparison dashboard...")
    dashboard_result = subprocess.run(
        ["poetry", "run", "python", "generate_v3_dashboard_comparison.py"],
        capture_output=True,
        text=True
    )
    
    if dashboard_result.returncode == 0:
        logger.info("✅ Comparison dashboard generated successfully!")
        logger.info("Check: results_v3/visualizations/schizobench_v3_dashboard_comparison.html")
        logger.info("This dashboard shows both standard and enhanced Opus 4 results side-by-side!")
    else:
        logger.error("❌ Dashboard generation failed!")
        if dashboard_result.stderr:
            logger.error(f"Error: {dashboard_result.stderr}")
        logger.info("Trying standard dashboard as fallback...")
        fallback = subprocess.run(
            ["poetry", "run", "python", "generate_v3_dashboard_dark.py"],
            capture_output=True,
            text=True
        )
        if fallback.returncode == 0:
            logger.info("✅ Standard dashboard generated as fallback")

if __name__ == "__main__":
    main()