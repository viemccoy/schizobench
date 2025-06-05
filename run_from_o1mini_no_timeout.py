#!/usr/bin/env python3
"""
Resume benchmark from O1-mini onwards - NO TIMEOUTS VERSION
Skips all completed models AND the problematic gpt-4.1-mini
Runs without any timeouts - models can take as long as needed
"""

import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple color codes for terminal
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('benchmark_no_timeout.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Model configurations starting from O1-mini (skipping problematic gpt-4.1-mini)
MODEL_CONFIGS = {
    "openai": [
        # SKIP: gpt-4.1-2025-04-14 - completed
        # SKIP: gpt-4.1-mini-2025-04-14 - failing with API errors
        {"model": "gpt-4.1-nano-2025-04-14"},
        # SKIP: gpt-4o-2024-08-06 - completed
        {"model": "gpt-4o-mini-2024-07-18"},
        # SKIP: o3-2025-04-16 - completed
        {"model": "o3-mini-2025-01-31", "temperature": 1.0},
        {"model": "o4-mini-2025-04-16", "temperature": 1.0},
        {"model": "o1-2024-12-17", "temperature": 1.0},
        {"model": "o1-mini-2024-09-12", "temperature": 1.0},
    ],
    
    "google": [
        {"model": "gemini-2.5-pro-preview-05-06"},
        {"model": "gemini-2.5-flash-preview-05-20"},
        {"model": "gemini-2.0-flash-exp"},
        {"model": "gemini-2.0-flash-lite"},
    ],
    
    "openrouter": [
        {"model": "deepseek/deepseek-r1-0528:free"},
        {"model": "deepseek/deepseek-chat-v3-0324:free"},
        {"model": "deepseek/deepseek-r1:free"},
        {"model": "deepseek/deepseek-chat:free"},
        {"model": "x-ai/grok-3-beta"},
        {"model": "x-ai/grok-3-mini-beta"},
        {"model": "x-ai/grok-2-1212"},
        {"model": "meta-llama/llama-4-maverick:free"},
        {"model": "meta-llama/llama-4-scout:free"},
        {"model": "meta-llama/llama-3.3-70b-instruct:free"},
        {"model": "meta-llama/llama-3.1-405b-instruct"},  # 405B!
        {"model": "meta-llama/llama-3.1-70b-instruct"},
        {"model": "meta-llama/llama-3-70b-instruct"},
        {"model": "nousresearch/hermes-3-llama-3.1-70b"},
        {"model": "nousresearch/hermes-3-llama-3.1-405b"},  # 405B!
    ]
}

def check_if_completed(provider: str, model: str) -> bool:
    """Check if a model has already been benchmarked"""
    results_dir = Path("results_v3")
    
    # Check for any JSON file with this model name
    for json_file in results_dir.glob("*.json"):
        if model.replace('/', '_') in str(json_file):
            return True
            
        # Also check inside the JSON
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if data.get('metadata', {}).get('model') == model:
                    logger.info(f"✓ Already completed: {provider}/{model}")
                    return True
        except:
            pass
    
    return False

def get_completed_count() -> int:
    """Count completed models"""
    results_dir = Path("results_v3")
    count = 0
    
    for json_file in results_dir.glob("*.json"):
        if 'transcripts' not in str(json_file):
            count += 1
    
    return count

def run_single_benchmark(provider: str, config: Dict, model_num: int, total_models: int) -> Tuple[bool, Optional[str]]:
    """Run benchmark for a single model WITHOUT TIMEOUT"""
    
    model = config["model"]
    temperature = config.get("temperature", 0.7)
    
    # Skip if already completed
    if check_if_completed(provider, model):
        return True, None
    
    logger.info(f"\n{'='*70}")
    logger.info(f"{Colors.CYAN}[{model_num}/{total_models}] {provider}/{model}{Colors.RESET}")
    logger.info(f"{Colors.YELLOW}NO TIMEOUT - Model can run as long as needed{Colors.RESET}")
    logger.info(f"Temperature: {temperature}")
    logger.info(f"{'='*70}\n")
    
    try:
        # Build command
        cmd = [
            "poetry", "run", "python", "run_benchmark_v3_robust.py",
            "--provider", provider,
            "--model", model,
            "--temperature", str(temperature),
            "--scoring-provider", "openai",
            "--scoring-model", "gpt-4.1-2025-04-14"
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        logger.info(f"{Colors.YELLOW}Running without timeout - press Ctrl+C to interrupt if needed{Colors.RESET}")
        
        # Run WITHOUT timeout
        start_time = time.time()
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream output
        while True:
            output = process.stdout.readline()
            if output:
                line = output.strip()
                if line:
                    # Highlight important messages
                    if "PROGRESS:" in line:
                        elapsed = time.time() - start_time
                        elapsed_min = elapsed / 60
                        logger.info(f"{Colors.GREEN}{line} [{elapsed_min:.1f}m elapsed]{Colors.RESET}")
                    elif "REIFICATION DETECTED" in line:
                        logger.info(f"{Colors.YELLOW}{line}{Colors.RESET}")
                    elif "error" in line.lower():
                        logger.info(f"{Colors.RED}{line}{Colors.RESET}")
                    else:
                        logger.info(f"[{model}] {line}")
            
            # Check if process finished
            if process.poll() is not None:
                break
        
        # Check return code
        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60
        
        if process.returncode == 0:
            logger.info(f"{Colors.GREEN}✓ Successfully completed {provider}/{model} in {elapsed_min:.1f} minutes{Colors.RESET}")
            return True, None
        else:
            error_msg = f"Process exited with code {process.returncode}"
            logger.error(f"{Colors.RED}✗ Failed: {error_msg} after {elapsed_min:.1f} minutes{Colors.RESET}")
            return False, error_msg
            
    except KeyboardInterrupt:
        logger.warning(f"{Colors.YELLOW}Interrupted by user. Terminating current model...{Colors.RESET}")
        process.terminate()
        time.sleep(5)
        if process.poll() is None:
            process.kill()
        raise
    except Exception as e:
        logger.error(f"{Colors.RED}✗ Exception: {str(e)}{Colors.RESET}")
        return False, str(e)

def main():
    """Main execution"""
    logger.info(f"{Colors.CYAN}{Colors.BOLD}")
    logger.info("="*70)
    logger.info("SchizoBench Resume from O1-mini - NO TIMEOUT VERSION")
    logger.info("(Skipping problematic gpt-4.1-mini)")
    logger.info("="*70)
    logger.info(f"{Colors.RESET}")
    
    # Get initial count
    completed_initial = get_completed_count()
    total_models = 38  # Total including Anthropic
    remaining_in_configs = sum(len(models) for models in MODEL_CONFIGS.values())
    
    logger.info(f"Starting with {completed_initial}/{total_models} models completed")
    logger.info(f"Will process up to {remaining_in_configs} remaining models")
    logger.info(f"{Colors.YELLOW}NO TIMEOUTS - Models will run to completion{Colors.RESET}")
    logger.info(f"{Colors.YELLOW}Skipping gpt-4.1-mini-2025-04-14 due to API errors{Colors.RESET}")
    
    # Track results
    results = {
        'completed': [],
        'failed': [],
        'skipped': ['openai/gpt-4.1-mini-2025-04-14']  # Pre-mark as skipped
    }
    
    model_counter = completed_initial + 1
    
    try:
        # Process each provider
        for provider, models in MODEL_CONFIGS.items():
            if not models:
                continue
                
            logger.info(f"\n{Colors.BLUE}Provider: {provider}{Colors.RESET}")
            
            for config in models:
                model = config['model']
                
                # Check if already completed
                if check_if_completed(provider, model):
                    results['skipped'].append(f"{provider}/{model}")
                    continue
                
                # Run benchmark
                success, error = run_single_benchmark(
                    provider, config, model_counter, total_models
                )
                
                if success:
                    results['completed'].append(f"{provider}/{model}")
                else:
                    results['failed'].append({
                        'model': f"{provider}/{model}",
                        'error': error
                    })
                
                model_counter += 1
                
                # Brief pause between models
                logger.info("Pausing 10 seconds before next model...")
                time.sleep(10)
    
    except KeyboardInterrupt:
        logger.warning(f"\n{Colors.YELLOW}Benchmark interrupted by user{Colors.RESET}")
    
    # Final summary
    logger.info(f"\n{Colors.CYAN}{'='*70}")
    logger.info("BENCHMARK SESSION SUMMARY")
    logger.info(f"{'='*70}{Colors.RESET}")
    
    logger.info(f"\n{Colors.GREEN}Completed this session: {len(results['completed'])}")
    for model in results['completed']:
        logger.info(f"  ✓ {model}")
    
    logger.info(f"\n{Colors.BLUE}Skipped (already done or problematic): {len(results['skipped'])}")
    for model in results['skipped']:
        logger.info(f"  - {model}")
    
    if results['failed']:
        logger.info(f"\n{Colors.RED}Failed: {len(results['failed'])}")
        for failure in results['failed']:
            logger.info(f"  ✗ {failure['model']}: {failure['error']}")
    
    # Save results summary
    with open('benchmark_no_timeout_summary.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'session_completed': len(results['completed']),
            'total_completed': completed_initial + len(results['completed'])
        }, f, indent=2)
    
    logger.info(f"\n{Colors.GREEN}Results saved to benchmark_no_timeout_summary.json{Colors.RESET}")
    logger.info(f"{Colors.CYAN}Run 'poetry run python generate_v3_dashboard_comprehensive.py' to create dashboard{Colors.RESET}")

if __name__ == "__main__":
    main()